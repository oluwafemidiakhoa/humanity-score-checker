"""Privileged offline helper for Humanity Score human claim review.

This command is intentionally NOT exposed as an MCP tool. A reviewer must inspect
an evidence JSON file and explicitly confirm that each finding is supported by
its signed source snapshot before the separate review key is used.

Usage:
  HUMANITY_SCORE_SIGNING_KEY=... \
  HUMANITY_SCORE_REVIEW_SIGNING_KEY=... \
  python review_cli.py input.json output.json --reviewer-id reviewer-a --confirm-supported

The input may be either a JSON array of evidence objects or an object containing
an "evidence" array.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from provenance import issue_claim_review_attestation, verify_snapshot_attestation


def _load_evidence(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        evidence = payload
    elif isinstance(payload, dict) and isinstance(payload.get("evidence"), list):
        evidence = payload["evidence"]
    else:
        raise ValueError('input must be a JSON array or object containing an "evidence" array')
    if not all(isinstance(item, dict) for item in evidence):
        raise ValueError("every evidence item must be a JSON object")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Privileged offline Humanity Score claim-review attestation helper"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument(
        "--confirm-supported",
        action="store_true",
        help="Required explicit confirmation that the reviewer inspected every finding against its source snapshot.",
    )
    args = parser.parse_args()

    if not args.confirm_supported:
        raise SystemExit(
            "Refusing to sign. Re-run with --confirm-supported only after a human reviewer "
            "has inspected every finding against its captured source."
        )

    evidence = _load_evidence(args.input)
    reviewed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    reviewed: list[dict[str, Any]] = []

    for index, item in enumerate(evidence):
        if not verify_snapshot_attestation(item):
            raise SystemExit(
                f"Evidence item {index} does not carry a valid Humanity Score source-snapshot attestation."
            )
        updated = dict(item)
        updated.update(
            issue_claim_review_attestation(
                updated,
                reviewer_id=args.reviewer_id,
                reviewed_at=reviewed_at,
            )
        )
        reviewed.append(updated)

    args.output.write_text(
        json.dumps(reviewed, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Signed {len(reviewed)} human-reviewed evidence claims for {args.reviewer_id}.")


if __name__ == "__main__":
    main()
