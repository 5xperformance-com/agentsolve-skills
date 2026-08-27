#!/usr/bin/env python3
"""Run a staff-rostering quote -> job -> poll example."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from urllib import error, request

PROBLEM_TYPE = "4.3.scheduling.rostering"
INPUT_SCHEMA_VERSION = "4.3.scheduling.rostering.input.v3"
OUTPUT_SCHEMA_VERSION = "4.3.scheduling.rostering.output.v2"
EXAMPLE_ID = "rostering-seeded-001"
CANONICAL_PROBLEM_HASH = "bb4053b9104856c212e82c2546c0e54d1794e0e6ac099944c4c756611d6055ff"
REST_FLOW = ["POST /v1/quotes", "POST /v1/jobs", "GET /v1/jobs/{job_id}"]
MCP_FLOW = [
    "agentsolve.quotes.create",
    "agentsolve.jobs.create",
    "agentsolve.jobs.get",
]

PAYLOAD = {
    "site_timezone": "Europe/London",
    "staff": [
        {"id": "sam", "skills": ["senior_nurse"], "max_hours": 8},
        {"id": "jules", "skills": ["junior_nurse"], "max_hours": 8},
    ],
    "skill_substitution": [["senior_nurse", "junior_nurse"]],
    "slots": [
        {
            "id": "monday-day",
            "start_utc": "2026-07-27T08:00:00Z",
            "end_utc": "2026-07-27T16:00:00Z",
            "requirements": [
                {"skill": "junior_nurse", "min_headcount": 1, "target_headcount": 2}
            ],
        }
    ],
    "penalties": {
        "under_target": 100,
        "over_target": 10,
        "weekend_deviation": 0,
        "night_deviation": 0,
        "hours_deviation": 0,
    },
}

DRY_RESULT = {
    "status": "optimal",
    "solver_status": "OPTIMAL",
    "assignments": [
        {"staff_id": "jules", "slot_id": "monday-day"},
        {"staff_id": "sam", "slot_id": "monday-day"},
    ],
    "objective_value": 0,
    "penalty_breakdown": {
        "under_target": 0,
        "over_target": 0,
        "weekend_deviation": 0,
        "night_deviation": 0,
        "hours_deviation": 0,
    },
}


def stable_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def canonical_problem_hash() -> str:
    return CANONICAL_PROBLEM_HASH


def request_json(
    method: str, url: str, body: dict[str, object] | None = None
) -> dict[str, object]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    token = os.environ.get("AGENTSOLVE_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    scopes = os.environ.get("AGENTSOLVE_DEV_SCOPES")
    if scopes:
        headers["x-agentsolve-scopes"] = scopes
    try:
        with request.urlopen(
            request.Request(url, data=data, headers=headers, method=method),
            timeout=30,
        ) as response:
            return json.loads(response.read().decode())
    except error.HTTPError as exc:
        message = f"{method} {url} failed with HTTP {exc.code}: {exc.read().decode()}"
        raise SystemExit(message) from exc


def quote_body() -> dict[str, object]:
    return {
        "idempotency_key": f"{EXAMPLE_ID}-quote",
        "problem_type": PROBLEM_TYPE,
        "problem_schema_version": INPUT_SCHEMA_VERSION,
        "input": PAYLOAD,
        "policy": {
            "max_price_usdc": "1.00",
            "exploration_mode": "none",
            "failover_mode": "strict",
            "allowed_regions": ["eu-west-1"],
        },
    }


def job_body(base: str, quote: dict[str, object]) -> dict[str, object]:
    body: dict[str, object] = {
        "idempotency_key": f"{EXAMPLE_ID}-job",
        "quote_token": quote["quote_token"],
    }
    default_candidate = quote.get("default_candidate_solver_admission_id")
    if isinstance(default_candidate, str) and default_candidate:
        body["selected_algorithms"] = [default_candidate]
    else:
        body["auto_route"] = True
    requirement = quote.get("payment_requirement")
    if isinstance(requirement, dict) and requirement.get("requires_payment") is False:
        return body
    trial_code = os.environ.get("AGENTSOLVE_TRIAL_CREDIT_CODE")
    if trial_code:
        body["payment"] = {"rail": "trial_credit", "trial_credit_code": trial_code}
    else:
        intent = request_json(
            "POST",
            f"{base}/v1/payments/stripe/payment-intents",
            {
                "quote_token": quote["quote_token"],
                "job_idempotency_key": f"{EXAMPLE_ID}-job",
                "idempotency_key": f"{EXAMPLE_ID}-pi",
            },
        )
        body["payment"] = {
            "rail": "stripe",
            "payment_intent_id": intent["payment_intent_id"],
        }
    return body


def dry_run() -> dict[str, object]:
    return {
        "mode": "dry_run",
        "problem_type": PROBLEM_TYPE,
        "problem_schema_version": INPUT_SCHEMA_VERSION,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "canonical_problem_hash": canonical_problem_hash(),
        "settled_result_hash": stable_hash(DRY_RESULT),
        "status": "SETTLED",
        "rest_flow": REST_FLOW,
        "mcp_flow": MCP_FLOW,
        "payload": PAYLOAD,
        "result": DRY_RESULT,
    }


def live_run(base_url: str) -> dict[str, object]:
    base = base_url.rstrip("/")
    quote = request_json("POST", f"{base}/v1/quotes", quote_body())
    job = request_json("POST", f"{base}/v1/jobs", job_body(base, quote))
    job_id = job.get("job_id")
    if not isinstance(job_id, str):
        raise SystemExit("job response did not include job_id")
    observed = job
    for _ in range(60):
        if observed.get("terminal") is True:
            break
        wait_ms = max(int(observed.get("recommended_poll_after_ms") or 100), 100)
        time.sleep(wait_ms / 1000)
        observed = request_json("GET", f"{base}/v1/jobs/{job_id}")
    return {"mode": "live", "quote": quote, "job": observed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("AGENTSOLVE_BASE_URL"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = dry_run() if args.dry_run or not args.base_url else live_run(args.base_url)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
