#!/usr/bin/env python3
"""Run the Stage 0 TSP quote -> job -> poll example."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from urllib import error, request

PROBLEM_TYPE = "1.1.tsp"
INPUT_SCHEMA_VERSION = "1.1.tsp.input.v1"
OUTPUT_SCHEMA_VERSION = "1.1.tsp.output.v1"
EXAMPLE_ID = "tsp-seeded-002"
CANONICAL_PROBLEM_HASH = "c58b8aef17e48643c52197573d9d0a33da509315c65e945db0c85a90d0af2d6b"
REST_FLOW = ["POST /v1/quotes", "POST /v1/jobs", "GET /v1/jobs/{job_id}"]
MCP_FLOW = [
    "agentsolve.quotes.create",
    "agentsolve.jobs.create",
    "agentsolve.jobs.get",
]

NODES = [
    "depot", "alpha", "bravo", "charlie", "delta", "echo",
    "foxtrot", "golf", "hotel", "india", "juliet", "kilo",
]

# Symmetric distances; row and column order follow NODES.
DISTANCE_ROWS = [
    [ 0,  7,  9,  9, 11, 10,  9,  8,  9,  9,  5,  3],
    [ 7,  0,  7, 11, 16, 17, 16, 13,  9,  5, 11,  6],
    [ 9,  7,  0,  6, 12, 16, 18, 17, 15, 12,  9, 10],
    [ 9, 11,  6,  0,  6, 11, 16, 17, 17, 16,  6, 12],
    [11, 16, 12,  6,  0,  6, 13, 17, 19, 19,  6, 13],
    [10, 17, 16, 11,  6,  0,  8, 13, 17, 18,  6, 12],
    [ 9, 16, 18, 16, 13,  8,  0,  6, 12, 15,  9, 10],
    [ 8, 13, 17, 17, 17, 13,  6,  0,  6, 10, 11,  7],
    [ 9,  9, 15, 17, 19, 17, 12,  6,  0,  5, 13,  6],
    [ 9,  5, 12, 16, 19, 18, 15, 10,  5,  0, 13,  6],
    [ 5, 11,  9,  6,  6,  6,  9, 11, 13, 13,  0,  8],
    [ 3,  6, 10, 12, 13, 12, 10,  7,  6,  6,  8,  0],
]

PAYLOAD = {
    "nodes": NODES,
    "start_node": "depot",
    "distances": {
        origin: {
            destination: DISTANCE_ROWS[row][column]
            for column, destination in enumerate(NODES)
            if destination != origin
        }
        for row, origin in enumerate(NODES)
    },
}

DRY_RESULT = {
    "route": [
        "depot", "kilo", "alpha", "india", "hotel", "golf", "foxtrot",
        "echo", "delta", "charlie", "bravo", "juliet", "depot",
    ],
    "objective_value": 71,
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
