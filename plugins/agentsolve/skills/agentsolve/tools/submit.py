#!/usr/bin/env python3
"""Submit translated canonical documents through quote -> job -> poll.

Reads one or more submission documents written by tools/translate.py, creates
a quote, resolves funding (account-credit authority first, then trial credit,
then an already-confirmed Stripe PaymentIntent, then an automatic faucet
fallback when the account is enrolled in an active faucet program), creates
the job, polls to a terminal state, and writes results named after the source
instance (`foo.tsp` -> `foo.result.json`, plus a TSPLIB `foo.tour` for
`1.1.tsp` and a CVRPLIB `foo.sol` for `1.2.vrp.cvrp`). Use `--out-dir` to
write them where your task expects (for example `--out-dir solutions`); the
default is the document's own directory.

Routing: the default runs the quote's default candidate solver — one engine,
one price. When the task asks for the best achievable answer, pass
`--portfolio` to run every eligible candidate on the quote (up to the cohort
cap of 10); the tool polls until the whole cohort finishes (reporting N/M
progress), obtains every settled member's result separately — one attributed
artifact per solver (`foo.<solver_admission_id>.result.json`, carrying that
member's own receipt), so a portfolio doubles as a benchmarking sweep — and
additionally emits the best result by the problem's objective sense as the
headline answer. `--select ID [ID ...]` submits an explicit cohort, and
`--auto-route` uses the platform's deterministic catalog-default selection.
`--settled-threshold N` stops waiting once N members have settled and ranks
exactly the first N responses by settlement order — receipt timestamps, so
"call ten, keep the best of the first three" holds even when more members
finish between polls; the remaining members keep running server-side
(portfolio cancellation is all-or-none, so nothing is cancelable once any
member starts). If the cohort terminalizes with fewer than N settled
members, or any ranked member's evidence cannot be written, the command
fails without a headline answer: a "best" drawn from a silently reduced
subset is not evidence. The job price multiplies by the cohort size, and portfolio jobs
pay from account credit or trial credit only; the Stripe rail rejects
portfolios by design.

Quote constraints: `--time-budget-ms N` buys the engines a solve-time
budget (the quote echoes the effective hints it bound), and
`--constraints JSON` passes any other quote constraint object. Both are
part of the idempotency key: re-quoting the same document with a larger
budget executes a fresh paid job instead of silently replaying the cheap
one. `--rerun` deliberately re-executes an identical submission (a paid
re-roll); without it, re-running the same command replays the previous
result at no extra cost.

`--quote-only` prices the submission (candidates, engines, price
ceiling, payment options) without creating a job. `--detach` creates the
job and exits immediately, printing the job id and the exact resume
command; `--resume JOB_ID` (with the same document) polls an existing
job to completion and writes results. `--receipts-dir` separates the
per-member receipt artifacts from the deliverables directory.

Usage:
    python tools/submit.py DOC.canonical.json [MORE.canonical.json ...]
        [--portfolio | --select ADMISSION_ID [ADMISSION_ID ...] | --auto-route]
        [--settled-threshold N]
        [--time-budget-ms N] [--constraints JSON] [--rerun]
        [--quote-only | --detach | --resume JOB_ID]
        [--max-price-usdc X] [--max-concurrency N] [--quiet | --json]
        [--base-url URL] [--out-dir DIR] [--receipts-dir DIR]
        [--poll-timeout SECONDS]

Environment: AGENTSOLVE_BASE_URL, AGENTSOLVE_API_TOKEN, AGENTSOLVE_DEV_SCOPES,
AGENTSOLVE_TRIAL_CREDIT_CODE, AGENTSOLVE_STRIPE_PAYMENT_INTENT_ID (an already
confirmed intent for the Stripe rail), AGENTSOLVE_MAX_PRICE_USDC (the price
ceiling per quote — default "1.00"; a portfolio's total is the SUM of member
prices and is checked against this same ceiling at job creation, so raise it
for large cohorts or pass --max-price-usdc).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

try:
    from translate import NativeFormatError, write_sol, write_tour
except ModuleNotFoundError:  # imported from outside tools/ (wrappers, tests)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from translate import NativeFormatError, write_sol, write_tour

TERMINAL_STATUSES = {"SETTLED", "REFUNDED", "DISPUTED", "SUPERSEDED"}
CAPTURABLE_INTENT_STATUSES = {"requires_capture", "succeeded"}
COHORT_CAP = 10
MAX_REQUEST_ATTEMPTS = 4
HEARTBEAT_SECONDS = 30.0


class FundingError(SystemExit):
    """No payment option was fundable; the message enumerates recoveries."""


def _retryable_rate_limit(status: int, detail: str) -> bool:
    """A 429 whose body does not explicitly say retryable=false."""
    if status != 429:
        return False
    try:
        parsed = json.loads(detail)
    except json.JSONDecodeError:
        return True

    def find(node: Any) -> bool | None:
        if isinstance(node, dict):
            if "retryable" in node:
                return bool(node["retryable"])
            for value in node.values():
                found = find(value)
                if found is not None:
                    return found
        return None

    found = find(parsed)
    return True if found is None else found


def request_json(method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    from urllib import error, request

    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    token = os.environ.get("AGENTSOLVE_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    scopes = os.environ.get("AGENTSOLVE_DEV_SCOPES")
    if scopes:
        headers["x-agentsolve-scopes"] = scopes
    attempt = 0
    while True:
        attempt += 1
        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode())
        except error.HTTPError as exc:
            detail = exc.read().decode()
            if _retryable_rate_limit(exc.code, detail) and attempt < MAX_REQUEST_ATTEMPTS:
                retry_after = exc.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else float(2**attempt)
                except ValueError:
                    delay = float(2**attempt)
                delay = min(delay, 30.0) + random.uniform(0.0, 0.5)
                print(
                    f"HTTP 429 on {method} {url}; retrying in {delay:.1f}s "
                    f"(attempt {attempt}/{MAX_REQUEST_ATTEMPTS})",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            raise SystemExit(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise SystemExit(
                f"{method} {url} failed before any HTTP response: {exc.reason}. "
                "If this runs in a network-restricted sandbox, allow access to "
                "the AgentSolve base URL and re-run."
            ) from exc


def load_document(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    for field in ("problem_type", "problem_schema_version", "payload"):
        if field not in document:
            raise SystemExit(f"{path}: submission document lacks {field!r}")
    return document


def source_stem(path: Path, document: dict[str, Any]) -> str:
    """The source instance's name without its native suffix (foo.tsp -> foo)."""
    name = document.get("source_file")
    if not isinstance(name, str) or not name:
        name = path.name
        if name.endswith(".canonical.json"):
            name = name[: -len(".canonical.json")]
    if name.endswith(".gz"):
        name = name[: -len(".gz")]
    stem, _, suffix = name.rpartition(".")
    return stem if stem and suffix else name


def routing_signature(routing: argparse.Namespace) -> str:
    if routing.auto_route:
        return "auto-route"
    if routing.select:
        return "select:" + ",".join(routing.select)
    if routing.portfolio:
        return "portfolio"
    return "default"


def quote_constraints(routing: argparse.Namespace) -> dict[str, Any] | None:
    """The quote constraints object this invocation asks for."""
    constraints: dict[str, Any] = {}
    extra = getattr(routing, "constraints", None)
    if isinstance(extra, dict):
        constraints.update(extra)
    time_budget_ms = getattr(routing, "time_budget_ms", None)
    if time_budget_ms is not None:
        constraints["time_budget_ms"] = time_budget_ms
    return constraints or None


def stable_key(path: Path, document: dict[str, Any], routing: argparse.Namespace) -> str:
    """Deterministic per (document, constraints, routing mode).

    The idempotency key covers everything that changes what the platform
    executes, so re-running an identical command replays the previous
    result while changing the time budget, constraints, or routing mode
    executes a fresh paid job. The client-side source filename stays out:
    renaming a file must not buy a re-execution. --rerun salts the key
    for a deliberate paid re-roll of an identical submission.
    """
    hashed_document = {k: v for k, v in document.items() if k != "source_file"}
    parts = [
        json.dumps(hashed_document, sort_keys=True, separators=(",", ":")),
        json.dumps(quote_constraints(routing) or {}, sort_keys=True, separators=(",", ":")),
        routing_signature(routing),
    ]
    if getattr(routing, "rerun", False):
        parts.append(f"rerun-{time.time_ns()}")
    digest = hashlib.sha256("\x00".join(parts).encode()).hexdigest()
    return f"{source_stem(path, document)}-{digest[:12]}"


def objective_sense(document: dict[str, Any]) -> str:
    """The direction "best" means for this document's objective_value.

    Each canonical class declares its direction its own way: LP/MILP carry
    ``objective.sense``, assignment a top-level ``sense``, newsvendor an
    ``objective`` string that starts with min/max; knapsack maximizes by
    definition, and every other launch class minimizes. Getting this wrong
    deliberately selects the worst solver in a portfolio.
    """
    payload = document.get("payload") or {}
    objective = payload.get("objective")
    if isinstance(objective, dict):
        sense = str(objective.get("sense", "")).lower()
        if sense in {"minimize", "min"}:
            return "min"
        if sense in {"maximize", "max"}:
            return "max"
    if isinstance(objective, str):
        if objective.startswith("max"):
            return "max"
        if objective.startswith("min"):
            return "min"
    payload_sense = str(payload.get("sense", "")).lower()
    if payload_sense == "max":
        return "max"
    if payload_sense == "min":
        return "min"
    if document.get("problem_type") == "9.1.knapsack":
        return "max"
    return "min"


def quote_body(
    key: str,
    document: dict[str, Any],
    *,
    constraints: dict[str, Any] | None = None,
    max_price_usdc: str | None = None,
    faucet_program_id: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "idempotency_key": (
            f"{key}-faucet-{faucet_program_id}" if faucet_program_id else f"{key}-quote"
        ),
        "problem_type": document["problem_type"],
        "problem_schema_version": document["problem_schema_version"],
        "input": document["payload"],
        "policy": {
            "max_price_usdc": (
                max_price_usdc or os.environ.get("AGENTSOLVE_MAX_PRICE_USDC", "1.00")
            ),
        },
    }
    if constraints:
        body["constraints"] = constraints
    if faucet_program_id:
        body["funding_mode"] = "faucet"
        body["faucet_program_id"] = faucet_program_id
    return body


def routing_fields(quote: dict[str, Any], routing: argparse.Namespace) -> dict[str, Any]:
    """The explicit routing mode for POST /v1/jobs.

    Default: the quote's default candidate — one engine, one price. The
    --portfolio flag submits every eligible candidate on the quote so a
    best-solution-seeking task compares engines instead of trusting one.
    """
    if routing.auto_route:
        return {"auto_route": True}
    if routing.select:
        return {"selected_algorithms": list(routing.select)}
    if routing.portfolio:
        candidate_ids = [
            candidate["solver_admission_id"]
            for candidate in quote.get("candidates", [])
            if isinstance(candidate, dict) and candidate.get("solver_admission_id")
        ]
        if not candidate_ids:
            raise SystemExit("--portfolio: the quote lists no candidates")
        if len(candidate_ids) > COHORT_CAP:
            print(
                f"--portfolio: quote lists {len(candidate_ids)} candidates; "
                f"submitting the first {COHORT_CAP} (cohort cap)",
                file=sys.stderr,
            )
            candidate_ids = candidate_ids[:COHORT_CAP]
        return {"selected_algorithms": candidate_ids}
    default_candidate = quote.get("default_candidate_solver_admission_id")
    if isinstance(default_candidate, str) and default_candidate:
        return {"selected_algorithms": [default_candidate]}
    return {"auto_route": True}


def resolve_stripe_payment(base: str, key: str, quote: dict[str, Any]) -> dict[str, Any]:
    preconfirmed = os.environ.get("AGENTSOLVE_STRIPE_PAYMENT_INTENT_ID")
    if preconfirmed:
        return {"rail": "stripe", "payment_intent_id": preconfirmed}
    intent = request_json(
        "POST",
        f"{base}/v1/payments/stripe/payment-intents",
        {
            "quote_token": quote["quote_token"],
            "job_idempotency_key": f"{key}-job",
            "idempotency_key": f"{key}-pi",
        },
    )
    status = str(intent.get("status"))
    if status in CAPTURABLE_INTENT_STATUSES:
        return {"rail": "stripe", "payment_intent_id": intent["payment_intent_id"]}
    # FundingError, not a plain exit: an unconfirmed intent must not block
    # the faucet fallback when the account is enrolled in one.
    raise FundingError(
        f"Stripe PaymentIntent {intent.get('payment_intent_id')} is "
        f"{status!r} and cannot fund a job yet: it must be confirmed on the "
        "Stripe side first (client_secret "
        f"{intent.get('client_secret')!r}). Complete that confirmation, then "
        "re-run with AGENTSOLVE_STRIPE_PAYMENT_INTENT_ID set to the "
        "confirmed intent id."
    )


def funding_failure_message(
    requirement: dict[str, Any],
    available: dict[str, Any],
    *,
    cohort_size: int,
) -> str:
    """Only recoveries this caller can actually take, from this quote."""
    lines = [
        "no fundable payment option; quote offered " + json.dumps(sorted(available))
    ]
    guidance = requirement.get("funding_guidance")
    if guidance:
        lines.append(f"quote guidance: {guidance}")
    options = {
        str(option.get("rail")): option
        for option in requirement.get("options", [])
        if isinstance(option, dict)
    }
    account_credit_reason = (options.get("account_credit") or {}).get("unavailable_reason")
    if account_credit_reason == "payment_authority_expired":
        lines.append(
            "recovery (requires the billing:write scope): the spend "
            "authority expired — create a fresh one "
            "(POST /v1/payments/authorities) and re-run"
        )
    elif account_credit_reason == "payment_authority_revoked":
        lines.append(
            "recovery (requires the billing:write scope): the spend "
            "authority was revoked — create a fresh one "
            "(POST /v1/payments/authorities) and re-run"
        )
    elif account_credit_reason:
        lines.append(f"account_credit unavailable: {account_credit_reason}")
    if "trial_credit" in available:
        lines.append(
            "recovery: the quote lists trial_credit as available — set "
            "AGENTSOLVE_TRIAL_CREDIT_CODE to a held code and re-run"
        )
    if cohort_size > 1 and "stripe" in available:
        lines.append(
            "portfolio jobs pay from account credit or trial credit; the "
            "Stripe rail rejects portfolios by design — fund account credit "
            "or submit a single candidate"
        )
    return "\n".join(lines)


def resolve_payment(
    base: str,
    key: str,
    quote: dict[str, Any],
    *,
    cohort_size: int = 1,
) -> dict[str, Any] | None:
    requirement = quote.get("payment_requirement")
    if not isinstance(requirement, dict) or requirement.get("requires_payment") is False:
        return None
    available = {
        str(option.get("rail")): option
        for option in requirement.get("options", [])
        if isinstance(option, dict) and option.get("available")
    }
    if "account_credit" in available:
        option = available["account_credit"]
        payment_object = (option.get("instructions") or {}).get("payment_object") or {}
        validated = payment_object.get("payment_authority_id")
        # The quote validated this specific authority for the caller, class,
        # and amount; guessing another one from the account-wide list can
        # submit an authority the server rejects.
        if (
            isinstance(validated, str)
            and validated.startswith("pauth_")
            and "..." not in validated
        ):
            return {"rail": "account_credit", "payment_authority_id": validated}
        listing = request_json("GET", f"{base}/v1/payments/authorities")
        for authority in listing.get("authorities", []):
            if authority.get("status") == "active" and "account_credit" in (
                authority.get("rails") or []
            ):
                return {
                    "rail": "account_credit",
                    "payment_authority_id": authority["payment_authority_id"],
                }
    trial_code = os.environ.get("AGENTSOLVE_TRIAL_CREDIT_CODE")
    if "trial_credit" in available and trial_code:
        return {"rail": "trial_credit", "trial_credit_code": trial_code}
    if "stripe" in available and cohort_size <= 1:
        return resolve_stripe_payment(base, key, quote)
    raise FundingError(
        funding_failure_message(requirement, available, cohort_size=cohort_size)
    )


def _drawable(program: dict[str, Any]) -> bool:
    try:
        return float(program.get("remaining_grant_usdc") or 0) > 0
    except (TypeError, ValueError):
        return False


def discover_faucet_programs(
    base: str,
    problem_type: str,
    quote: dict[str, Any],
) -> list[str]:
    """Drawable faucet programs to try in order: the quote's advertisement
    first (already filtered to this problem type), then the account listing."""
    program_ids: list[str] = []
    requirement = quote.get("payment_requirement")
    if isinstance(requirement, dict):
        for program in requirement.get("faucet_programs") or []:
            if isinstance(program, dict) and program.get("program_id") and _drawable(program):
                program_ids.append(str(program["program_id"]))
    try:
        listing = request_json("GET", f"{base}/v1/payments/faucet-programs")
    except SystemExit:
        listing = {}
    for program in listing.get("programs", []):
        if not isinstance(program, dict) or not program.get("program_id"):
            continue
        allowed = program.get("allowed_problem_types")
        if allowed is not None and problem_type not in allowed:
            continue
        if not _drawable(program):
            continue
        if str(program["program_id"]) not in program_ids:
            program_ids.append(str(program["program_id"]))
    return program_ids


def job_body(
    key: str,
    quote: dict[str, Any],
    routing_body: dict[str, Any],
    payment: dict[str, Any] | None,
    *,
    faucet_program_id: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "idempotency_key": (
            f"{key}-faucet-{faucet_program_id}-job" if faucet_program_id else f"{key}-job"
        ),
        "quote_token": quote["quote_token"],
    }
    body.update(routing_body)
    effective_hints = quote.get("effective_solver_hints")
    if effective_hints:
        body["solver_hints"] = effective_hints
    if payment is not None:
        body["payment"] = payment
    return body


def poll_job(
    base: str,
    job: dict[str, Any],
    timeout_seconds: float,
    *,
    settled_threshold: int | None = None,
    label: str = "job",
    quiet: bool = False,
) -> dict[str, Any]:
    """Poll until the whole request is finished.

    ``terminal`` is the aggregate signal: a portfolio head can be SETTLED
    while siblings still run, so status alone must never stop the poll when
    ``terminal`` is present. Progress lines are labelled with the instance
    so concurrent submissions stay legible, a heartbeat reports elapsed
    time during silent stretches, and the settled threshold stops the wait
    once at least N members have settled (the remaining members keep
    running server-side; portfolio cancellation is all-or-none). A poll
    may observe more than N settlements at once — ranking to exactly the
    first N by settlement order happens downstream from receipt
    timestamps.
    """

    def note(message: str) -> None:
        if not quiet:
            print(f"{label}: {message}", file=sys.stderr)

    job_id = job.get("job_id") or job.get("id")
    if not job_id:
        raise SystemExit("job response did not include job_id")
    started = time.monotonic()
    deadline = started + timeout_seconds
    observed = job
    last_progress: tuple[int, int, int] | None = None
    last_note = started

    def finished(final: dict[str, Any]) -> dict[str, Any]:
        members = final.get("cohort_members") or []
        if members:
            terminal_count = sum(1 for member in members if member.get("terminal"))
            settled_count = sum(
                1 for member in members if member.get("status") == "SETTLED"
            )
            note(
                f"cohort complete: {terminal_count}/{len(members)} members "
                f"terminal ({settled_count} settled)"
            )
        return final

    while time.monotonic() < deadline:
        terminal = observed.get("terminal")
        if terminal is True:
            return finished(observed)
        if terminal is None and str(observed.get("status")) in TERMINAL_STATUSES:
            return finished(observed)
        members = observed.get("cohort_members") or []
        now = time.monotonic()
        if members:
            terminal_count = sum(1 for member in members if member.get("terminal"))
            settled_count = sum(
                1 for member in members if member.get("status") == "SETTLED"
            )
            progress = (terminal_count, settled_count, len(members))
            if progress != last_progress:
                note(
                    f"cohort progress: {terminal_count}/{len(members)} members "
                    f"terminal ({settled_count} settled)"
                )
                last_progress = progress
                last_note = now
            if settled_threshold is not None and settled_count >= settled_threshold:
                note(
                    f"settled threshold reached ({settled_count}/{len(members)}); "
                    "ranking the first settled responses now — unfinished "
                    "members keep running server-side"
                )
                return observed
        if now - last_note >= HEARTBEAT_SECONDS:
            note(
                f"still waiting on {job_id} ({int(now - started)}s elapsed, "
                f"status {observed.get('status')})"
            )
            last_note = now
        wait_ms = int(observed.get("recommended_poll_after_ms") or 1000)
        time.sleep(max(wait_ms, 100) / 1000)
        observed = request_json("GET", f"{base}/v1/jobs/{job_id}")
    raise SystemExit(f"job {job_id} did not reach a terminal state within {timeout_seconds}s")


def _solver_label(member: dict[str, Any]) -> str:
    """The engine's human name: backend and version off the member's own
    receipt, with the admission id as the fallback identity."""
    receipt = member.get("routing_receipt")
    if isinstance(receipt, dict):
        backend = receipt.get("solver_backend")
        version = receipt.get("solver_version")
        if backend and version:
            return f"{backend}-{version}"
        if backend:
            return str(backend)
        identity = (
            receipt.get("solver_slot")
            or receipt.get("engine_lineage_id")
            or receipt.get("solver_admission_id")
        )
        if identity:
            return str(identity)
    return str(member.get("job_id"))


def _filename_safe(label: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "-" for char in label)


def _settlement_order_key(member: dict[str, Any]) -> tuple[str, int]:
    """Settlement order: receipt timestamp first, advertisement order as the
    tie-break; a member without a timestamp sorts last."""
    receipt = member.get("routing_receipt")
    recorded_at = (
        str(receipt.get("recorded_at")) if isinstance(receipt, dict) and receipt.get("recorded_at")
        else "9999"
    )
    position = member.get("cohort_position")
    return (recorded_at, position if position is not None else 0)


def collect_member_results(
    base: str,
    members: list[dict[str, Any]],
    document: dict[str, Any],
    stem: str,
    destination: Path,
    sense: str,
    *,
    settled_threshold: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], str | None, list[str]]:
    """Obtain every ranked member's result separately, then rank them.

    Each settled member in scope has its output fetched on its own and
    written as its own artifact (`{stem}.{engine}.result.json`, named by
    the engine off the member's own receipt), attributed via that receipt
    — a portfolio is a benchmarking sweep, and a result that is not
    separately recorded and attributed is lost to the comparison. With a
    settled threshold the scope is exactly the first N members by
    settlement order (receipt timestamps), even when more settled between
    polls; without one it is every settled member. The best ranked result
    by objective sense additionally becomes the headline answer. A
    refunded member contributes nothing. A ranked member whose evidence
    cannot be written is a failure the caller must see — silently
    incomplete benchmark evidence is worse than none.
    """
    summaries: list[dict[str, Any]] = []
    best_output: dict[str, Any] = {}
    best_job_id: str | None = None
    failures: list[str] = []
    ordered = sorted(
        members,
        key=lambda member: (
            member.get("cohort_position") if member.get("cohort_position") is not None else 0
        ),
    )
    settled = [member for member in ordered if member.get("status") == "SETTLED"]
    if settled_threshold is not None:
        ranked = sorted(settled, key=_settlement_order_key)[:settled_threshold]
    else:
        ranked = settled
    ranked_ids = {member.get("job_id") for member in ranked}
    for member in ordered:
        receipt = member.get("routing_receipt")
        entry: dict[str, Any] = {
            "job_id": member.get("job_id"),
            "status": member.get("status"),
            "solver_admission_id": (
                receipt.get("solver_admission_id") if isinstance(receipt, dict) else None
            ),
            "engine": _solver_label(member) if isinstance(receipt, dict) else None,
            "execution_time_ms": (
                receipt.get("execution_time_ms") if isinstance(receipt, dict) else None
            ),
            "ranked": member.get("job_id") in ranked_ids,
        }
        summaries.append(entry)
        if not entry["ranked"]:
            continue
        output_url = member.get("output_url")
        if not output_url:
            failures.append(
                f"{member.get('job_id')}: settled but advertises no output_url"
            )
            continue
        try:
            output = request_json("GET", f"{base}{output_url}")
        except SystemExit as exc:
            failures.append(f"{member.get('job_id')}: output not readable: {exc}")
            continue
        member_path = destination / (
            f"{stem}.{_filename_safe(_solver_label(member))}.result.json"
        )
        member_path.write_text(
            json.dumps(
                {
                    "problem_type": document["problem_type"],
                    "problem_schema_version": document["problem_schema_version"],
                    "job_id": member.get("job_id"),
                    "status": member.get("status"),
                    "solver_admission_id": entry["solver_admission_id"],
                    "routing_receipt": receipt,
                    "output": output,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        entry["result"] = str(member_path)
        value = output.get("objective_value")
        entry["objective_value"] = value
        if best_job_id is None:
            best_output, best_job_id = output, member.get("job_id")
            continue
        incumbent = best_output.get("objective_value")
        if value is None:
            continue
        if incumbent is None or (value > incumbent if sense == "max" else value < incumbent):
            best_output, best_job_id = output, member.get("job_id")
    return summaries, best_output, best_job_id, failures


def _integral(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def write_native_solution(
    document: dict[str, Any],
    output: dict[str, Any],
    stem: str,
    out_dir: Path,
) -> str | None:
    numbering = document.get("node_numbering")
    if not numbering:
        return None
    problem_type = document["problem_type"]
    if problem_type == "1.1.tsp" and isinstance(output.get("route"), list):
        tour_path = out_dir / f"{stem}.tour"
        tour_path.write_text(
            write_tour(output["route"], tuple(numbering), stem), encoding="utf-8"
        )
        return str(tour_path)
    if problem_type == "1.2.vrp.cvrp" and isinstance(output.get("routes"), list):
        routes = [
            [stop["node_id"] for stop in route.get("stops", [])]
            for route in output["routes"]
        ]
        sol_path = out_dir / f"{stem}.sol"
        sol_path.write_text(
            write_sol(routes, tuple(numbering), _integral(output.get("objective_value"))),
            encoding="utf-8",
        )
        return str(sol_path)
    return None


def _create_job_with_funding(
    base: str,
    key: str,
    document: dict[str, Any],
    quote: dict[str, Any],
    routing: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Resolve funding and create the job, falling back across every
    drawable faucet program when no ordinary rail is fundable.

    Returns (job, active quote, routing body, funding rail). Each faucet
    program gets its own quote and job idempotency keys, and a quote or
    job failure against one program moves on to the next instead of
    ending the command.
    """
    routing_body = routing_fields(quote, routing)
    cohort_size = len(routing_body.get("selected_algorithms", [])) or 1
    if routing.settled_threshold is not None and routing.settled_threshold >= cohort_size:
        raise SystemExit(
            f"--settled-threshold {routing.settled_threshold} must be below "
            f"the cohort size ({cohort_size}); omit it to wait for the whole "
            "cohort"
        )
    try:
        payment = resolve_payment(base, key, quote, cohort_size=cohort_size)
    except FundingError as unresolved:
        attempts: list[str] = []
        for program_id in discover_faucet_programs(base, document["problem_type"], quote):
            try:
                candidate = request_json(
                    "POST",
                    f"{base}/v1/quotes",
                    quote_body(
                        key,
                        document,
                        constraints=quote_constraints(routing),
                        max_price_usdc=getattr(routing, "max_price_usdc", None),
                        faucet_program_id=program_id,
                    ),
                )
            except SystemExit as exc:
                attempts.append(f"{program_id}: quote failed: {exc}")
                continue
            requirement = candidate.get("payment_requirement") or {}
            if requirement.get("requires_payment") is not False:
                attempts.append(f"{program_id}: quote still requires payment")
                continue
            # The faucet quote has its own candidate set; re-resolve the
            # cohort against it and revalidate the threshold — a program
            # that restricts solver families can shrink the cohort below N.
            faucet_routing = routing_fields(candidate, routing)
            faucet_cohort = len(faucet_routing.get("selected_algorithms", [])) or 1
            if (
                routing.settled_threshold is not None
                and routing.settled_threshold >= faucet_cohort
            ):
                attempts.append(
                    f"{program_id}: cohort resolves to {faucet_cohort} "
                    f"candidate(s), not above --settled-threshold "
                    f"{routing.settled_threshold}"
                )
                continue
            try:
                job = request_json(
                    "POST",
                    f"{base}/v1/jobs",
                    job_body(
                        key,
                        candidate,
                        faucet_routing,
                        None,
                        faucet_program_id=program_id,
                    ),
                )
            except SystemExit as exc:
                attempts.append(f"{program_id}: job creation failed: {exc}")
                continue
            print(
                f"funding fell back to faucet program {program_id}",
                file=sys.stderr,
            )
            return job, candidate, faucet_routing, f"faucet ({program_id})"
        detail = (
            "; ".join(attempts)
            if attempts
            else "no drawable faucet enrollment covers this problem type"
        )
        raise SystemExit(f"{unresolved}\nfaucet fallback: {detail}") from unresolved
    try:
        job = request_json(
            "POST", f"{base}/v1/jobs", job_body(key, quote, routing_body, payment)
        )
    except SystemExit as exc:
        if "portfolio_total_exceeds_price_ceiling" in str(exc):
            raise SystemExit(
                f"{exc}\nrecovery: a portfolio's price is the SUM of its "
                "member prices, checked against the quote's max_price_usdc "
                "ceiling at job creation — re-run with --max-price-usdc at or "
                "above the cohort total (or export AGENTSOLVE_MAX_PRICE_USDC; "
                "default 1.00), or narrow the cohort with --select"
            ) from exc
        raise
    rail = payment["rail"] if payment else "none required (requires_payment=false)"
    return job, quote, routing_body, rail


def _print_warnings(label: str, container: dict[str, Any], quiet: bool) -> None:
    """Job and quote warnings reach the console when they matter, not
    buried at the tail of a result blob."""
    if quiet:
        return
    for warning in container.get("warnings") or []:
        if isinstance(warning, dict):
            print(
                f"{label}: warning {warning.get('code')}: {warning.get('message')}",
                file=sys.stderr,
            )


def _quote_summary(path: Path, quote: dict[str, Any]) -> dict[str, Any]:
    """Price an experiment before buying it: candidates with engine names
    and per-member prices, the ceiling, and the payment options."""
    requirement = quote.get("payment_requirement") or {}
    return {
        "input_document": str(path),
        "quote_id": quote.get("quote_id"),
        "complexity_tier": quote.get("complexity_tier"),
        "price_ceiling_usdc": quote.get("price_ceiling_usdc"),
        "effective_solver_hints": quote.get("effective_solver_hints"),
        "candidates": [
            {
                "solver_admission_id": candidate.get("solver_admission_id"),
                "engine": (
                    f"{candidate.get('solver_slot')}"
                    + (f" v{candidate['solver_version']}" if candidate.get("solver_version") else "")
                ),
                "price_locked_usdc": candidate.get("price_locked_usdc"),
            }
            for candidate in quote.get("candidates") or []
            if isinstance(candidate, dict)
        ],
        "default_candidate_solver_admission_id": quote.get(
            "default_candidate_solver_admission_id"
        ),
        "requires_payment": requirement.get("requires_payment"),
        "payment_options": [
            {"rail": option.get("rail"), "available": option.get("available")}
            for option in requirement.get("options") or []
            if isinstance(option, dict)
        ],
        "warnings": quote.get("warnings") or [],
    }


def _objective_spread_note(
    stem: str, cohort: list[dict[str, Any]], quiet: bool
) -> None:
    ranked = [
        entry
        for entry in cohort
        if entry.get("ranked") and entry.get("objective_value") is not None
    ]
    if quiet or len(ranked) < 2:
        return
    values = [entry["objective_value"] for entry in ranked]
    parts = ", ".join(
        f"{entry.get('engine') or entry.get('solver_admission_id')}="
        f"{entry['objective_value']}"
        for entry in ranked
    )
    print(
        f"{stem}: cohort objectives: {parts} "
        f"(spread {max(values) - min(values)})",
        file=sys.stderr,
    )


def submit_one(
    base: str,
    path: Path,
    timeout_seconds: float,
    out_dir: Path | None,
    routing: argparse.Namespace,
) -> dict[str, Any]:
    document = load_document(path)
    stem = source_stem(path, document)
    destination = out_dir if out_dir is not None else path.parent
    destination.mkdir(parents=True, exist_ok=True)
    receipts_dir = getattr(routing, "receipts_dir", None)
    receipts_destination = receipts_dir if receipts_dir is not None else destination
    receipts_destination.mkdir(parents=True, exist_ok=True)
    quiet = bool(getattr(routing, "quiet", False))
    resume_job_id = getattr(routing, "resume", None)
    funding_rail: str | None = None
    if resume_job_id:
        job: dict[str, Any] = {"job_id": resume_job_id}
    else:
        key = stable_key(path, document, routing)
        quote = request_json(
            "POST",
            f"{base}/v1/quotes",
            quote_body(
                key,
                document,
                constraints=quote_constraints(routing),
                max_price_usdc=getattr(routing, "max_price_usdc", None),
            ),
        )
        if not (quote.get("quote_id") or quote.get("id")):
            raise SystemExit(f"{path}: quote response did not include quote_id")
        _print_warnings(stem, quote, quiet)
        if getattr(routing, "quote_only", False):
            return _quote_summary(path, quote)
        job, quote, _, funding_rail = _create_job_with_funding(
            base, key, document, quote, routing
        )
        if not quiet:
            print(
                f"{stem}: funding rail {funding_rail}; "
                f"price_locked_usdc {job.get('price_locked_usdc')}",
                file=sys.stderr,
            )
        if getattr(routing, "detach", False):
            return {
                "input_document": str(path),
                "job_id": job.get("job_id"),
                "status": job.get("status"),
                "funding_rail": funding_rail,
                "price_locked_usdc": job.get("price_locked_usdc"),
                "detached": True,
                "resume": (
                    f"python tools/submit.py {path} --resume {job.get('job_id')}"
                    + (f" --out-dir {out_dir}" if out_dir is not None else "")
                ),
            }
    observed = poll_job(
        base,
        job,
        timeout_seconds,
        settled_threshold=routing.settled_threshold,
        label=stem,
        quiet=quiet,
    )
    _print_warnings(stem, observed, quiet)
    advisory = observed.get("improvement_advisory")
    if advisory and not quiet:
        print(f"{stem}: {advisory}", file=sys.stderr)

    members = observed.get("cohort_members") or []
    selected_job_id: str | None = observed.get("job_id")
    settled_members: str | None = None
    cohort: list[dict[str, Any]] = []
    failures: list[str] = []
    if members:
        cohort, output, selected_job_id, failures = collect_member_results(
            base,
            members,
            document,
            stem,
            receipts_destination,
            objective_sense(document),
            settled_threshold=routing.settled_threshold,
        )
        settled_count = sum(1 for entry in cohort if entry.get("status") == "SETTLED")
        settled_members = f"{settled_count}/{len(members)}"
        if (
            routing.settled_threshold is not None
            and settled_count < routing.settled_threshold
        ):
            failures.append(
                f"cohort terminalized with {settled_count} settled member(s); "
                f"--settled-threshold {routing.settled_threshold} cannot be "
                "satisfied"
            )
        if routing.settled_threshold is None and settled_count < len(members):
            # A partial cohort without an explicit threshold is a loud
            # failure, never a bare SETTLED headline from the remnant.
            shortfall = ", ".join(
                f"{member.get('job_id')} {member.get('status')}"
                + (
                    f" ({(member.get('terminal_diagnostic') or {}).get('failure_code')})"
                    if isinstance(member.get("terminal_diagnostic"), dict)
                    and (member.get("terminal_diagnostic") or {}).get("failure_code")
                    else ""
                )
                for member in members
                if member.get("status") != "SETTLED"
            )
            failures.append(
                f"cohort delivered {settled_count}/{len(members)} settled "
                f"members without --settled-threshold; non-settled: "
                f"{shortfall}"
            )
    else:
        output = observed.get("output") if isinstance(observed.get("output"), dict) else {}
        if str(observed.get("status")) != "SETTLED":
            diagnostic = observed.get("terminal_diagnostic")
            code = (
                diagnostic.get("failure_code") if isinstance(diagnostic, dict) else None
            )
            failures.append(
                f"job {observed.get('job_id')} terminalized "
                f"{observed.get('status')}" + (f" ({code})" if code else "")
            )
    # No headline or native answer on incomplete evidence: a "best" chosen
    # from a silently reduced subset looks like a normal result and is
    # worse than an explicit failure. A previous run's headline files are
    # removed too — a stale answer surviving a failed rerun reads as
    # current. Attributed member artifacts written above are preserved.
    if failures:
        for stale in (
            destination / f"{stem}.result.json",
            destination / f"{stem}.tour",
            destination / f"{stem}.sol",
        ):
            stale.unlink(missing_ok=True)
        raise SystemExit(
            f"{path}: cohort evidence incomplete — "
            + "; ".join(failures)
            + f"; attributed member artifacts remain in {receipts_destination}; no "
            "headline answer exists for this instance"
        )
    _objective_spread_note(stem, cohort, quiet)
    result_path = destination / f"{stem}.result.json"
    record = {
        "input_document": str(path),
        "problem_type": document["problem_type"],
        "problem_schema_version": document["problem_schema_version"],
        "status": observed.get("status"),
        # The headline number at the top level — no nested archaeology.
        "objective_value": (output or {}).get("objective_value"),
        "job": observed,
    }
    if members:
        # The headline answer is the selected member's output, not the
        # cohort head's, and the selected member's own receipt attests it.
        record["output"] = output
        record["selected_job_id"] = selected_job_id
        record["selected_member_receipt"] = next(
            (
                member.get("routing_receipt")
                for member in members
                if member.get("job_id") == selected_job_id
            ),
            None,
        )
        record["settled_members"] = settled_members
        record["cohort"] = cohort
    result_path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    native_solution: str | None = None
    try:
        native_solution = write_native_solution(document, output or {}, stem, destination)
    except NativeFormatError as exc:
        print(f"{path}: native solution not written: {exc}", file=sys.stderr)
    summary = {
        "input_document": str(path),
        "status": observed.get("status"),
        "objective_value": (output or {}).get("objective_value"),
        "result": str(result_path),
        "native_solution": native_solution,
        "price_locked_usdc": observed.get("price_locked_usdc"),
    }
    if funding_rail is not None:
        summary["funding_rail"] = funding_rail
    if advisory:
        summary["improvement_advisory"] = advisory
    if members:
        summary["selected_job_id"] = selected_job_id
        summary["settled_members"] = settled_members
        summary["cohort"] = cohort
    return summary


def _price_total(summaries: list[dict[str, Any]]) -> str | None:
    from decimal import Decimal, InvalidOperation

    total = Decimal("0")
    seen = False
    for summary in summaries:
        price = summary.get("price_locked_usdc")
        if price is None:
            continue
        try:
            total += Decimal(str(price))
        except InvalidOperation:
            return None
        seen = True
    return str(total) if seen else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Submit translated canonical documents through quote -> job -> "
            "poll. Routing default: the quote's default candidate (one "
            "engine, one price); --portfolio runs every eligible candidate "
            "(up to 10), polls the whole cohort with N/M progress, writes "
            "one attributed result per settled member, and emits the best "
            "by objective sense, at cohort-size times the price."
        )
    )
    parser.add_argument("documents", nargs="+", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--portfolio",
        action="store_true",
        help=(
            "run every eligible candidate on the quote (cohort cap 10), "
            "write one attributed result artifact per settled member, and "
            "emit the best by objective sense; price multiplies by cohort "
            "size. Pays from account credit or trial credit only."
        ),
    )
    mode.add_argument(
        "--select",
        nargs="+",
        metavar="ADMISSION_ID",
        help="run an explicit candidate cohort (1 id for a single engine, 2-10 for a portfolio)",
    )
    mode.add_argument(
        "--auto-route",
        action="store_true",
        help="use the platform's deterministic catalog-default selection",
    )
    parser.add_argument(
        "--settled-threshold",
        type=int,
        default=None,
        metavar="N",
        help=(
            "stop waiting once N cohort members have settled and rank "
            "exactly the first N responses by settlement order; unfinished "
            "members keep running server-side (portfolio cancellation is "
            "all-or-none). Requires a multi-member cohort and N below the "
            "cohort size."
        ),
    )
    parser.add_argument(
        "--time-budget-ms",
        type=int,
        default=None,
        metavar="N",
        help=(
            "quote constraint: solve-time budget in milliseconds, folded "
            "into the engines' effective hints (the quote echoes what it "
            "bound). Part of the idempotency key: a changed budget executes "
            "a fresh paid job instead of replaying"
        ),
    )
    parser.add_argument(
        "--constraints",
        type=str,
        default=None,
        metavar="JSON",
        help=(
            "additional quote constraints as a JSON object (merged with "
            "--time-budget-ms, which wins on conflict); part of the "
            "idempotency key"
        ),
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        help=(
            "deliberately re-execute an identical submission as a fresh "
            "PAID job (salts the idempotency key); without it, re-running "
            "the same command replays the previous result at no extra cost"
        ),
    )
    lifecycle = parser.add_mutually_exclusive_group()
    lifecycle.add_argument(
        "--quote-only",
        action="store_true",
        help=(
            "price the submission and stop: print candidates with engine "
            "names and per-member prices, the price ceiling, and payment "
            "options, without creating a job"
        ),
    )
    lifecycle.add_argument(
        "--detach",
        action="store_true",
        help=(
            "create the job and exit immediately, printing the job id and "
            "the exact --resume command; poll later instead of blocking"
        ),
    )
    lifecycle.add_argument(
        "--resume",
        type=str,
        default=None,
        metavar="JOB_ID",
        help=(
            "poll an existing job to completion and write results (pass the "
            "same document the job was created from; exactly one document)"
        ),
    )
    parser.add_argument(
        "--max-price-usdc",
        type=str,
        default=None,
        metavar="X",
        help=(
            "price ceiling for the quote (default: AGENTSOLVE_MAX_PRICE_USDC "
            "or 1.00). A portfolio's total is the SUM of member prices and "
            "is checked against this same ceiling at job creation — raise "
            "it for large cohorts"
        ),
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=3,
        metavar="N",
        help=(
            "process up to N documents concurrently inside this one "
            "process (default 3; 1 = strictly serial). Progress lines are "
            "instance-labelled, and in-tool batching avoids the rate-limit "
            "collisions of parallel processes"
        ),
    )
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument(
        "--quiet",
        action="store_true",
        help="suppress progress and heartbeat lines (warnings still print)",
    )
    output_mode.add_argument(
        "--json",
        action="store_true",
        help=(
            "machine mode: stdout carries only the final JSON summary; all "
            "progress, heartbeat, and price lines are suppressed"
        ),
    )
    parser.add_argument("--base-url", default=os.environ.get("AGENTSOLVE_BASE_URL"))
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="directory for result/native-solution files (default: beside each document)",
    )
    parser.add_argument(
        "--receipts-dir",
        type=Path,
        default=None,
        help=(
            "directory for per-member receipt artifacts "
            "({stem}.{engine}.result.json); default: the deliverables "
            "directory. Keeps graded output directories pristine"
        ),
    )
    parser.add_argument("--poll-timeout", type=float, default=900.0)
    args = parser.parse_args()
    if not args.base_url:
        raise SystemExit("set AGENTSOLVE_BASE_URL or pass --base-url")
    if args.settled_threshold is not None:
        if args.settled_threshold < 1:
            raise SystemExit("--settled-threshold must be at least 1")
        if not args.portfolio and not (args.select and len(args.select) > 1):
            raise SystemExit(
                "--settled-threshold applies to multi-member cohorts; pass "
                "--portfolio or --select with two or more ids"
            )
    if args.constraints is not None:
        try:
            parsed_constraints = json.loads(args.constraints)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--constraints is not valid JSON: {exc}") from exc
        if not isinstance(parsed_constraints, dict):
            raise SystemExit("--constraints must be a JSON object")
        args.constraints = parsed_constraints
    if args.resume and len(args.documents) != 1:
        raise SystemExit("--resume polls one job: pass exactly one document")
    if args.max_concurrency < 1:
        raise SystemExit("--max-concurrency must be at least 1")
    args.quiet = args.quiet or args.json
    base = args.base_url.rstrip("/")

    def run_one(path: Path) -> dict[str, Any]:
        return submit_one(base, path, args.poll_timeout, args.out_dir, args)

    failures: list[str] = []
    if len(args.documents) == 1 or args.max_concurrency == 1:
        summaries: list[dict[str, Any]] = []
        for path in args.documents:
            try:
                summaries.append(run_one(path))
            except SystemExit as exc:
                failures.append(str(exc))
                summaries.append({"input_document": str(path), "error": str(exc)})
    else:
        from concurrent.futures import ThreadPoolExecutor

        workers = min(args.max_concurrency, len(args.documents))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_one, path) for path in args.documents]
            summaries = []
            for path, future in zip(args.documents, futures):
                try:
                    summaries.append(future.result())
                except SystemExit as exc:
                    failures.append(str(exc))
                    summaries.append({"input_document": str(path), "error": str(exc)})
    print(json.dumps(summaries, indent=2, sort_keys=True))
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    if not args.quiet and not args.quote_only and not args.detach:
        total = _price_total(summaries)
        if total is not None:
            print(
                f"total price_locked_usdc across {len(summaries)} "
                f"document(s): {total}",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
