#!/usr/bin/env python3
"""Solve native optimization instances end to end in one invocation.

Runs translate -> quote -> fund -> submit -> poll -> write as a single
foreground call: native instance files (TSPLIB `.tsp`/`.atsp`, CVRPLIB
`.vrp`, MPS `.mps`/`.mps.gz`, PSPLIB single-mode `.sm`, Taillard) are
translated deterministically first, canonical `*.canonical.json`
documents pass through unchanged, and everything then follows
tools/submit.py exactly — the same flags, funding self-heal, polling
discipline, answer block, and `--json` machine summary. Canonical
documents land in the working directory; input directories stay
pristine.

Usage:
    python tools/solve.py INSTANCE_OR_DOC [MORE ...]
        [any tools/submit.py option]
        [--format {tsplib,cvrplib,mps,psplib-sm,taillard}]
        [--vehicle-count N] [--instance-index K]

One invocation is the intended shape: the tool waits in the foreground
(the poll deadline follows the purchased budget plus dispatch headroom)
and finishes with the receipt-backed answer block, so no background
launch, log tailing, or artifact re-reading is needed afterwards. When
a purchased budget exceeds the patience of a foreground call, --detach
and --resume still decouple submission from waiting.

A failed translation is loud and buys nothing: no quote or job is
created for any input when one of them cannot be translated.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import submit
    import translate
except ModuleNotFoundError:  # imported from outside tools/ (wrappers, tests)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import submit
    import translate


def _is_canonical_document(path: Path) -> bool:
    if not path.name.endswith(".json"):
        return False
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(document, dict) and all(
        field in document
        for field in ("problem_type", "problem_schema_version", "payload")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = submit.build_parser()
    parser.description = (
        "Translate native optimization instances and drive them through "
        "quote -> job -> poll in one foreground invocation. Canonical "
        "documents pass through unchanged; every tools/submit.py option "
        "applies."
    )
    parser.add_argument(
        "--format",
        dest="format_id",
        choices=[
            translate.FORMAT_TSPLIB,
            translate.FORMAT_CVRPLIB,
            translate.FORMAT_MPS,
            translate.FORMAT_PSPLIB_SM,
            translate.FORMAT_TAILLARD,
        ],
        default=None,
        help="override native-format detection for non-canonical inputs",
    )
    parser.add_argument(
        "--vehicle-count",
        type=int,
        default=None,
        help="CVRPLIB vehicle count when the file does not declare one",
    )
    parser.add_argument(
        "--instance-index",
        type=int,
        default=0,
        help="which instance to take from a multi-instance Taillard file",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    # Plan every final document path first and refuse collisions before
    # anything is written or bought: two inputs sharing a basename would
    # silently overwrite one canonical document and submit the other
    # twice, losing an instance without an error.
    plan: list[tuple[Path, Path | None]] = []
    claimed: dict[Path, Path] = {}
    failures: list[str] = []
    for path in args.documents:
        target = (
            path
            if _is_canonical_document(path)
            else Path.cwd() / f"{path.name}.canonical.json"
        )
        resolved = target.resolve()
        if resolved in claimed:
            failures.append(
                f"solve: {path} and {claimed[resolved]} both resolve to "
                f"{target.name}; rename one input — nothing was written or "
                "submitted"
            )
            continue
        claimed[resolved] = path
        plan.append((path, None if target == path else target))
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    documents: list[Path] = []
    for path, target in plan:
        if target is None:
            documents.append(path)
            continue
        try:
            document = translate.translate_native(
                path,
                format_id=args.format_id,
                vehicle_count=args.vehicle_count,
                instance_index=args.instance_index,
            )
        except (translate.NativeFormatError, OSError) as exc:
            failures.append(f"solve: {path}: {exc}")
            continue
        target.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        documents.append(target)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    args.documents = documents
    return submit.run(args)


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    sys.exit(main())
