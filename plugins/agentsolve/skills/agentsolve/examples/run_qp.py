#!/usr/bin/env python3
"""Run the Stage 0 QP quote -> job -> poll example."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from urllib import error, request

PROBLEM_TYPE = "2.3.qp"
INPUT_SCHEMA_VERSION = "2.3.qp.input.v1"
OUTPUT_SCHEMA_VERSION = "2.3.qp.output.v1"
EXAMPLE_ID = "qp-blend-seeded-001"
CANONICAL_PROBLEM_HASH = "962860d4416c0f3ec18f1a892f8578b01284d7f34decd7ad967c31f2e4f22139"
REST_FLOW = ["POST /v1/quotes", "POST /v1/jobs", "GET /v1/jobs/{job_id}"]
MCP_FLOW = [
    "agentsolve.quotes.create",
    "agentsolve.jobs.create",
    "agentsolve.jobs.get",
]

PAYLOAD = {
    "id": EXAMPLE_ID,
    "variables": {
        "oats": {"type": "continuous", "lb": 0, "ub": 0.6},
        "barley": {"type": "continuous", "lb": 0, "ub": 0.6},
        "peas": {"type": "continuous", "lb": 0, "ub": 0.6},
        "bran": {"type": "continuous", "lb": 0, "ub": 0.6},
    },
    "constraints": [
        {
            "id": "one_batch",
            "function": {
                "type": "linear",
                "coefficients": {"oats": 1, "barley": 1, "peas": 1, "bran": 1},
                "constant": -1,
            },
            "set": {"type": "zeros"},
        },
        {
            "id": "protein_floor",
            "function": {
                "type": "linear",
                "coefficients": {"oats": 11, "barley": 10, "peas": 22, "bran": 15},
                "constant": -14,
            },
            "set": {"type": "nonneg"},
        },
    ],
    "objective": {
        "id": "min_energy_variance",
        "sense": "minimize",
        "function": {
            "type": "quadratic",
            "quadratic_terms": [
                {"x": "oats", "y": "oats", "coeff": 0.04},
                {"x": "oats", "y": "barley", "coeff": 0.012},
                {"x": "oats", "y": "peas", "coeff": 0.008},
                {"x": "oats", "y": "bran", "coeff": 0.004},
                {"x": "barley", "y": "barley", "coeff": 0.09},
                {"x": "barley", "y": "peas", "coeff": 0.02},
                {"x": "barley", "y": "bran", "coeff": 0.006},
                {"x": "peas", "y": "peas", "coeff": 0.16},
                {"x": "peas", "y": "bran", "coeff": 0.01},
                {"x": "bran", "y": "bran", "coeff": 0.25},
            ],
            "linear_terms": {"oats": 0.003, "barley": 0.002, "peas": 0.006, "bran": 0.001},
            "constant": 0,
        },
    },
    "metadata": {"tags": ["single-objective-blending-qp"]},
}

DRY_RESULT = {
    "objective_value": 0.0310541,
    "variable_values": {
        "oats": 0.483446,
        "barley": 0.157386,
        "peas": 0.245817,
        "bran": 0.113351,
    },
    "dual_values": {
        "one_batch": 0.00084161,
        "protein_floor": -0.0042569,
    },
    "reduced_costs": None,
    "optimality_gap": 0,
    "best_bound": 0.0310541,
    "solver_status": "OPTIMAL",
}


def stable_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def canonical_problem_hash() -> str:
    return CANONICAL_PROBLEM_HASH


def request_json(method: str, url: str, body: dict[str, object] | None = None) -> dict[str, object]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    token = os.environ.get("AGENTSOLVE_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    scopes = os.environ.get("AGENTSOLVE_DEV_SCOPES")
    if scopes:
        headers["x-agentsolve-scopes"] = scopes
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except error.HTTPError as exc:
        detail = exc.read().decode()
        raise SystemExit(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc


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
    payment_requirement = quote.get("payment_requirement")
    if (
        isinstance(payment_requirement, dict)
        and payment_requirement.get("requires_payment") is False
    ):
        return body

    payment: dict[str, object]
    trial_credit_code = os.environ.get("AGENTSOLVE_TRIAL_CREDIT_CODE")
    if trial_credit_code:
        payment = {"rail": "trial_credit", "trial_credit_code": trial_credit_code}
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
        payment = {"rail": "stripe", "payment_intent_id": intent["payment_intent_id"]}
    body["payment"] = payment
    return body


def dry_run() -> dict[str, object]:
    return {
        "mode": "dry_run",
        "example_id": EXAMPLE_ID,
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
    quote_id = quote.get("quote_id") or quote.get("id")
    if not quote_id:
        raise SystemExit("quote response did not include quote_id")

    job = request_json(
        "POST",
        f"{base}/v1/jobs",
        job_body(base, quote),
    )
    job_id = job.get("job_id") or job.get("id")
    if not job_id:
        raise SystemExit("job response did not include job_id")

    terminal = {"SETTLED", "REFUNDED", "DISPUTED", "SUPERSEDED"}
    observed = job
    for _ in range(60):
        if str(observed.get("status")) in terminal or observed.get("terminal") is True:
            break
        wait_ms = int(observed.get("recommended_poll_after_ms") or 1000)
        time.sleep(max(wait_ms, 100) / 1000)
        observed = request_json("GET", f"{base}/v1/jobs/{job_id}")

    return {
        "mode": "live",
        "example_id": EXAMPLE_ID,
        "problem_type": PROBLEM_TYPE,
        "problem_schema_version": INPUT_SCHEMA_VERSION,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "canonical_problem_hash": canonical_problem_hash(),
        "status": observed.get("status"),
        "quote": quote,
        "job": observed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("AGENTSOLVE_BASE_URL"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output = dry_run() if args.dry_run or not args.base_url else live_run(args.base_url)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
