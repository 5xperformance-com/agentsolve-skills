#!/usr/bin/env python3
"""Run the Stage 0 newsvendor quote -> job -> poll example."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from urllib import error, request

PROBLEM_TYPE = "3.1.newsvendor"
INPUT_SCHEMA_VERSION = "3.1.newsvendor.input.v1"
OUTPUT_SCHEMA_VERSION = "3.1.newsvendor.output.v1"
EXAMPLE_ID = "newsvendor-seeded-001"
CANONICAL_PROBLEM_HASH = "b2999d6ce7fe641b2c4e08e58ce29f06f05309c9fd71b226e7bb1ef68c0f230a"
REST_FLOW = ["POST /v1/quotes", "POST /v1/jobs", "GET /v1/jobs/{job_id}"]
MCP_FLOW = [
    "agentsolve.quotes.create",
    "agentsolve.jobs.create",
    "agentsolve.jobs.get",
]

PAYLOAD = {
    "id": EXAMPLE_ID,
    "objective": "max_expected_profit",
    "items": [
        {
            "sku_id": "meal_kit_a",
            "unit_cost": 8.0,
            "selling_price": 14.0,
            "salvage_value": 3.0,
            "stockout_penalty": 1.0,
            "min_order_qty": 0,
            "max_order_qty": 60,
            "order_step": 5,
            "demand_scenarios": [
                {"label": "low", "demand_qty": 20, "probability": 0.25},
                {"label": "base", "demand_qty": 35, "probability": 0.5},
                {"label": "high", "demand_qty": 50, "probability": 0.25},
            ],
        }
    ],
}

DRY_RESULT = {
    "problem_type": PROBLEM_TYPE,
    "problem_schema_version": INPUT_SCHEMA_VERSION,
    "output_schema_version": OUTPUT_SCHEMA_VERSION,
    "status": "SETTLED",
    "solver_status": "OPTIMAL",
    "objective_value": 151.25,
    "order_quantities": {"meal_kit_a": 35},
    "receipt_version": "receipt.v3",
}


def stable_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def canonical_problem_hash() -> str:
    return CANONICAL_PROBLEM_HASH


def request_json(method: str, url: str, body: dict[str, object] | None = None) -> dict[str, object]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
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
            "service_tier": "standard",
            "max_price_usdc": "0.20",
            "exploration_mode": "none",
            "failover_mode": "strict",
            "allowed_regions": ["us-east-1"],
        },
    }


def job_body(quote: dict[str, object]) -> dict[str, object]:
    body: dict[str, object] = {
        "idempotency_key": f"{EXAMPLE_ID}-job",
        "quote_token": quote["quote_token"],
        "auto_route": True,
    }
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
        payment = {"rail": "stripe", "payment_intent_id": f"pi_{EXAMPLE_ID}"}
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
        "status": DRY_RESULT["status"],
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
        job_body(quote),
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
