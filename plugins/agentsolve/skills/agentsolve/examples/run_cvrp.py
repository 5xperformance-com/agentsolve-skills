#!/usr/bin/env python3
"""Run the Stage 0 CVRP fleet-sizing/VRPTW-lite quote -> job -> poll example."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from urllib import error, request

PROBLEM_TYPE = "1.2.vrp.cvrp"
INPUT_SCHEMA_VERSION = "1.2.vrp.cvrp.input.v4"
OUTPUT_SCHEMA_VERSION = "1.2.vrp.cvrp.output.v4"
EXAMPLE_ID = "cvrp-vrptw-lite-seeded-001"
CANONICAL_PROBLEM_HASH = "2d8fc5f68d69c0b2aead657426d84b0330d626da8e45659c8f187121264c83e7"
REST_FLOW = ["POST /v1/quotes", "POST /v1/jobs", "GET /v1/jobs/{job_id}"]
MCP_FLOW = [
    "agentsolve.quotes.create",
    "agentsolve.jobs.create",
    "agentsolve.jobs.get",
]

PAYLOAD = {
    "id": EXAMPLE_ID,
    "job_intent": "optimize",
    "depot": {"id": "depot"},
    "vehicle_count": 2,
    "vehicle_capacity": 8,
    "vehicle_fixed_cost": 5,
    "vehicles": [{"id": "van_1", "capacity": 8}, {"id": "van_2", "capacity": 8}],
    "customers": [
        {"id": "alpha", "demand": 3},
        {"id": "bravo", "demand": 4},
        {"id": "charlie", "demand": 2, "eligible_vehicles": ["van_2"]},
    ],
    "distances": {
        "depot": {"alpha": 4, "bravo": 6, "charlie": 8},
        "alpha": {"depot": 4, "bravo": 3, "charlie": 7},
        "bravo": {"depot": 6, "alpha": 3, "charlie": 2},
        "charlie": {"depot": 8, "alpha": 7, "bravo": 2},
    },
    "travel_times": {
        "depot": {"alpha": 4, "bravo": 6, "charlie": 8},
        "alpha": {"depot": 4, "bravo": 3, "charlie": 7},
        "bravo": {"depot": 6, "alpha": 3, "charlie": 2},
        "charlie": {"depot": 8, "alpha": 7, "bravo": 2},
    },
    "time_windows": {
        "depot": [0, 30],
        "alpha": [4, 14],
        "bravo": [5, 18],
        "charlie": [8, 24],
    },
    "service_times": {"depot": 0, "alpha": 1, "bravo": 1, "charlie": 1},
    "route_duration_limit": 30,
}

DRY_RESULT = {
    "routes": [
        {
            "vehicle_id": "van_1",
            "stops": [
                {"node_id": "depot", "cumulative_load": 0},
                {
                    "node_id": "alpha",
                    "cumulative_load": 3,
                    "arrival_time": 4,
                    "service_start_time": 4,
                    "service_completion_time": 5,
                },
                {
                    "node_id": "bravo",
                    "cumulative_load": 7,
                    "arrival_time": 8,
                    "service_start_time": 8,
                    "service_completion_time": 9,
                },
                {
                    "node_id": "depot",
                    "cumulative_load": 7,
                    "arrival_time": 15,
                    "service_start_time": 15,
                    "service_completion_time": 15,
                },
            ],
            "load": 7,
            "distance": 13,
            "duration": 15,
        },
        {
            "vehicle_id": "van_2",
            "stops": [
                {"node_id": "depot", "cumulative_load": 0},
                {
                    "node_id": "charlie",
                    "cumulative_load": 2,
                    "arrival_time": 8,
                    "service_start_time": 8,
                    "service_completion_time": 9,
                },
                {
                    "node_id": "depot",
                    "cumulative_load": 2,
                    "arrival_time": 17,
                    "service_start_time": 17,
                    "service_completion_time": 17,
                },
            ],
            "load": 2,
            "distance": 16,
            "duration": 17,
        },
    ],
    "total_distance": 29,
    "total_fixed_cost": 10,
    "total_cost": 39,
    "objective_value": 39,
    "solver_status": "FEASIBLE",
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
