"""Reviewer calibration, disagreement, and appeal records for Humanity Score."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from core import DIMENSIONS, normalize_evidence, valid_http_url


def _hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compare_reviewer_evidence(
    reviewer_a: list[dict[str, Any]],
    reviewer_b: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare two independent coding passes over the same audit evidence.

    Matching is based on dimension/criterion/claim_id after normalization.
    The result does not resolve disagreements automatically; it makes them
    inspectable for adjudication.
    """

    def normalize_set(items: list[dict[str, Any]]) -> tuple[dict[tuple[str, str, str], dict[str, Any]], list[dict[str, Any]]]:
        out: dict[tuple[str, str, str], dict[str, Any]] = {}
        rejected: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            normalized, error = normalize_evidence(item)
            if normalized is None:
                rejected.append({"index": index, "reason": error})
                continue
            key = (normalized["dimension"], normalized["criterion"], normalized["claim_id"])
            out[key] = normalized
        return out, rejected

    a, rejected_a = normalize_set(reviewer_a)
    b, rejected_b = normalize_set(reviewer_b)
    keys = sorted(set(a) | set(b))

    agreements = 0
    disagreements: list[dict[str, Any]] = []
    overlap = 0

    for key in keys:
        left = a.get(key)
        right = b.get(key)
        if left is None or right is None:
            disagreements.append(
                {
                    "dimension": key[0],
                    "criterion": key[1],
                    "claim_id": key[2],
                    "type": "coverage_disagreement",
                    "reviewer_a": left,
                    "reviewer_b": right,
                }
            )
            continue

        overlap += 1
        if left["impact"] == right["impact"] and abs(left["confidence"] - right["confidence"]) <= 0.10:
            agreements += 1
            continue

        disagreements.append(
            {
                "dimension": key[0],
                "criterion": key[1],
                "claim_id": key[2],
                "type": "coding_disagreement",
                "impact_delta": right["impact"] - left["impact"],
                "confidence_delta": round(right["confidence"] - left["confidence"], 3),
                "reviewer_a": left,
                "reviewer_b": right,
            }
        )

    exact_agreement_rate = round(agreements / overlap, 3) if overlap else None
    return {
        "schema": "humanity-score.reviewer-comparison.v1",
        "claims_reviewer_a": len(a),
        "claims_reviewer_b": len(b),
        "overlapping_claims": overlap,
        "exact_agreements": agreements,
        "exact_agreement_rate": exact_agreement_rate,
        "disagreements": disagreements,
        "rejected_reviewer_a": rejected_a,
        "rejected_reviewer_b": rejected_b,
        "notice": (
            "Reviewer comparison is a calibration aid. Disagreements require documented "
            "adjudication; the tool does not silently average reviewer judgments."
        ),
    }


def create_appeal_record(
    *,
    product_name: str,
    report_hash: str,
    appellant: str,
    claim: str,
    evidence_urls: list[str],
    requested_correction: str,
) -> dict[str, Any]:
    """Create a deterministic appeal/correction intake record."""

    normalized_hash = report_hash.strip().lower()
    if len(normalized_hash) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_hash):
        raise ValueError("report_hash must be a 64-character SHA-256 hex digest")
    if not product_name.strip() or len(product_name.strip()) > 200:
        raise ValueError("product_name is required and must not exceed 200 characters")
    if not appellant.strip() or len(appellant.strip()) > 500:
        raise ValueError("appellant is required and must not exceed 500 characters")
    if len(claim.strip()) < 20 or len(claim.strip()) > 5000:
        raise ValueError("claim must contain 20 to 5000 characters")
    if len(requested_correction.strip()) < 10 or len(requested_correction.strip()) > 5000:
        raise ValueError("requested_correction must contain 10 to 5000 characters")
    if len(evidence_urls) > 50:
        raise ValueError("evidence_urls must not contain more than 50 URLs")
    invalid_urls = [url for url in evidence_urls if url.strip() and not valid_http_url(url.strip())]
    if invalid_urls:
        raise ValueError("all evidence_urls must use http(s)")

    submitted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "schema": "humanity-score.appeal.v1",
        "product_name": product_name.strip(),
        "report_hash": normalized_hash,
        "appellant": appellant.strip(),
        "claim": claim.strip(),
        "evidence_urls": sorted({url.strip() for url in evidence_urls if url.strip()}),
        "requested_correction": requested_correction.strip(),
        "submitted_at": submitted_at,
        "status": "open",
        "resolution": None,
    }
    payload["appeal_id"] = _hash({k: v for k, v in payload.items() if k != "submitted_at"})[:20]
    return payload


def rubric_coverage_template() -> list[dict[str, str]]:
    """Return the complete criterion set for reviewer calibration."""

    rows: list[dict[str, str]] = []
    for dimension, criteria in DIMENSIONS.items():
        for criterion in criteria:
            rows.append({"dimension": dimension, "criterion": criterion})
    return rows
