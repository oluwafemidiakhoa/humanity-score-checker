"""Core scoring logic for Humanity Score Checker.

Product 3.1 introduces methodology 3.0: unknown criteria are no longer silently
treated as neutral, duplicate claims are de-duplicated, contradictory evidence
is surfaced, and independently retrieved source snapshots can be attached to
findings.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, urlunparse

from provenance import verify_claim_review_attestation, verify_snapshot_attestation

PRODUCT_VERSION = "3.3.1"
RUBRIC_VERSION = "3.2.1"

MAX_PRODUCT_NAME_CHARS = 200
MAX_DESCRIPTION_CHARS = 10_000
MAX_HUMAN_STORY_CHARS = 10_000
MAX_FINDING_CHARS = 5_000
MAX_EVIDENCE_ITEMS = 200

DIMENSIONS: dict[str, tuple[str, ...]] = {
    "agency": (
        "user_control",
        "reversibility",
        "transparency",
        "human_override",
    ),
    "value_distribution": (
        "user_benefit",
        "data_rights",
        "lock_in",
        "incentive_alignment",
    ),
    "human_connection": (
        "collaboration",
        "substitution_risk",
        "social_wellbeing",
        "accessibility",
    ),
}

DIMENSION_ALIASES = {
    "value_capture": "value_distribution",
    "connection": "human_connection",
}

SOURCE_WEIGHTS = {
    "primary": 1.0,
    "secondary": 0.75,
    "anecdotal": 0.50,
}

IMPACT_ANCHORS = {
    -2: "Strong, directly supported evidence of material harm, loss of control, exclusion, or adverse incentive.",
    -1: "Supported evidence of a meaningful concern or downside.",
    0: "Supported evidence is mixed, neutral, or does not justify directional movement.",
    1: "Supported evidence of a meaningful benefit, control, safeguard, or positive outcome.",
    2: "Strong, directly supported evidence of a material benefit, safeguard, or positive outcome.",
}

CONFIDENCE_ANCHORS = {
    "low": "Material ambiguity, indirect evidence, or unresolved interpretation.",
    "moderate": "Evidence substantially supports the finding but leaves meaningful uncertainty.",
    "high": "Direct, specific evidence with little interpretive uncertainty.",
}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        _ = parsed.port
    except (TypeError, ValueError):
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def source_site(value: str) -> str:
    """Return a conservative site key so subdomains do not count as independent sources."""
    host = (urlparse(value).hostname or "").lower().rstrip(".")
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    common_second_level = {"co", "com", "org", "net", "gov", "ac", "edu"}
    if len(parts[-1]) == 2 and parts[-2] in common_second_level and len(parts) >= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def canonical_url(value: str) -> str:
    parsed = urlparse(value.strip())
    host = parsed.hostname.lower() if parsed.hostname else ""
    port = parsed.port
    if port and not (
        (parsed.scheme == "http" and port == 80)
        or (parsed.scheme == "https" and port == 443)
    ):
        netloc = f"{host}:{port}"
    else:
        netloc = host
    path = parsed.path or "/"
    return urlunparse((parsed.scheme.lower(), netloc, path, "", parsed.query, ""))


def badge_band(score: int) -> tuple[str, str]:
    if score >= 70:
        return "green", "GREEN"
    if score >= 40:
        return "yellow", "YELLOW"
    return "red", "RED"


def _score_inputs(*values: int) -> None:
    for value in values:
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            raise ValueError("Scores must be integers from 0 to 100.")


def _valid_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value))


def _valid_iso_datetime(value: str) -> bool:
    if not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _normalized_text(value: str) -> str:
    return " ".join(value.lower().split())


def _claim_fingerprint(dimension: str, criterion: str, finding: str) -> str:
    payload = f"{dimension}|{criterion}|{_normalized_text(finding)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def score_self_reported(
    *,
    product_name: str,
    description: str,
    agency: int,
    value_capture: int,
    connection: int,
    sources: list[str],
    human_story: str,
    product_url: str = "",
) -> dict[str, Any]:
    """Compatibility scoring path for the original interface.

    The result is intentionally marked self-reported and is never eligible for
    an evidence-backed badge.
    """

    _score_inputs(agency, value_capture, connection)
    score = round((agency + value_capture + connection) / 3)
    color, band = badge_band(score)
    source_urls = sorted(
        {
            canonical_url(s.strip())
            for s in sources
            if isinstance(s, str) and valid_http_url(s.strip())
        }
    )
    documentation_gate = len(source_urls) >= 2 and len(human_story.strip()) >= 20

    return {
        "product_version": PRODUCT_VERSION,
        "humanity_score": score,
        "dimension_scores": {
            "agency": agency,
            "value_distribution": value_capture,
            "human_connection": connection,
        },
        "badge_color": color,
        "badge_label": f"SELF-ASSESSED {band}",
        "badge_eligible": False,
        "assessment_mode": "self_reported",
        "documentation_gate_passed": documentation_gate,
        "sources_recognized": source_urls,
        "product_name": product_name,
        "product_url": product_url,
        "description": description,
        "human_story": human_story,
        "rubric_version": RUBRIC_VERSION,
        "notice": (
            "Self-reported scores are not evidence-backed audits and cannot receive "
            "an evidence-backed Humanity Score badge. Use audit_product with structured evidence."
        ),
    }


def normalize_evidence(item: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(item, dict):
        return None, "evidence item must be an object"

    dimension = str(item.get("dimension", "")).strip().lower()
    dimension = DIMENSION_ALIASES.get(dimension, dimension)
    criterion = str(item.get("criterion", "")).strip().lower()
    finding = str(item.get("finding", "")).strip()
    source = str(item.get("source", "")).strip()
    source_type = str(item.get("source_type", "")).strip().lower()
    rationale = str(item.get("rationale", "")).strip()
    reviewer_id = str(item.get("reviewer_id", "")).strip()
    claim_id = str(item.get("claim_id", "")).strip()
    source_snapshot_sha256 = str(item.get("source_snapshot_sha256", "")).strip().lower()
    source_retrieved_at = str(item.get("source_retrieved_at", "")).strip()
    source_archive_url = str(item.get("source_archive_url", "")).strip()
    source_snapshot_content_type = str(item.get("source_snapshot_content_type", "")).strip()
    source_snapshot_signature = str(item.get("source_snapshot_signature", "")).strip()
    source_snapshot_key_id = str(item.get("source_snapshot_key_id", "")).strip()
    claim_review_status = str(item.get("claim_review_status", "")).strip().lower()
    claim_review_reviewer_id = str(item.get("claim_review_reviewer_id", "")).strip()
    claim_reviewed_at = str(item.get("claim_reviewed_at", "")).strip()
    claim_review_product_name = str(item.get("claim_review_product_name", "")).strip()
    claim_review_product_url = str(item.get("claim_review_product_url", "")).strip()
    claim_support_excerpt = str(item.get("claim_support_excerpt", "")).strip()
    claim_review_signature = str(item.get("claim_review_signature", "")).strip()
    claim_review_key_id = str(item.get("claim_review_key_id", "")).strip()
    try:
        source_snapshot_bytes = int(item.get("source_snapshot_bytes", 0) or 0)
    except (TypeError, ValueError):
        return None, "source_snapshot_bytes must be an integer"

    try:
        impact_raw = float(item.get("impact"))
        confidence = float(item["confidence"])
    except (KeyError, TypeError, ValueError):
        return None, "impact and confidence are required and must be numeric"

    if not impact_raw.is_integer() or int(impact_raw) not in IMPACT_ANCHORS:
        return None, "impact must be one of -2, -1, 0, 1, or 2"
    impact = int(impact_raw)

    if dimension not in DIMENSIONS:
        return None, f"unknown dimension: {dimension or '<empty>'}"
    if criterion not in DIMENSIONS[dimension]:
        return None, f"unknown criterion '{criterion}' for dimension '{dimension}'"
    if len(finding) < 20:
        return None, "finding must contain at least 20 characters"
    if len(finding) > MAX_FINDING_CHARS:
        return None, f"finding must not exceed {MAX_FINDING_CHARS} characters"
    if not valid_http_url(source):
        return None, "source must be an http(s) URL"
    if source_type not in SOURCE_WEIGHTS:
        return None, "source_type must be primary, secondary, or anecdotal"
    if confidence < 0 or confidence > 1:
        return None, "confidence must be between 0 and 1"

    if source_snapshot_sha256 and not _valid_sha256(source_snapshot_sha256):
        return None, "source_snapshot_sha256 must be a 64-character SHA-256 hex digest"
    if source_retrieved_at and not _valid_iso_datetime(source_retrieved_at):
        return None, "source_retrieved_at must be an ISO-8601 datetime with timezone"
    if bool(source_snapshot_sha256) != bool(source_retrieved_at):
        return None, "source_snapshot_sha256 and source_retrieved_at must be supplied together"
    if source_archive_url and not valid_http_url(source_archive_url):
        return None, "source_archive_url must be an http(s) URL"

    source = canonical_url(source)
    snapshot_present = any(
        [
            source_snapshot_sha256,
            source_retrieved_at,
            source_snapshot_content_type,
            source_snapshot_signature,
            source_snapshot_key_id,
            source_snapshot_bytes,
        ]
    )
    source_verified = False
    if snapshot_present:
        source_verified = verify_snapshot_attestation(
            {
                "source": source,
                "source_snapshot_sha256": source_snapshot_sha256,
                "source_retrieved_at": source_retrieved_at,
                "source_snapshot_content_type": source_snapshot_content_type,
                "source_snapshot_bytes": source_snapshot_bytes,
                "source_snapshot_signature": source_snapshot_signature,
                "source_snapshot_key_id": source_snapshot_key_id,
            }
        )

    resolved_claim_id = claim_id or _claim_fingerprint(dimension, criterion, finding)

    claim_review_verified = verify_claim_review_attestation(
        {
            "dimension": dimension,
            "criterion": criterion,
            "finding": finding,
            "source": source,
            "source_type": source_type,
            "impact": impact,
            "confidence": confidence,
            "claim_id": resolved_claim_id,
            "source_snapshot_sha256": source_snapshot_sha256,
            "source_retrieved_at": source_retrieved_at,
            "source_snapshot_content_type": source_snapshot_content_type,
            "source_snapshot_bytes": source_snapshot_bytes,
            "source_snapshot_signature": source_snapshot_signature,
            "source_snapshot_key_id": source_snapshot_key_id,
            "claim_review_status": claim_review_status,
            "claim_review_reviewer_id": claim_review_reviewer_id,
            "claim_reviewed_at": claim_reviewed_at,
            "claim_review_product_name": claim_review_product_name,
            "claim_review_product_url": claim_review_product_url,
            "claim_support_excerpt": claim_support_excerpt,
            "claim_review_signature": claim_review_signature,
            "claim_review_key_id": claim_review_key_id,
        }
    )

    return {
        "dimension": dimension,
        "criterion": criterion,
        "finding": finding,
        "source": source,
        "source_type": source_type,
        "impact": impact,
        "confidence": confidence,
        "rationale": rationale,
        "reviewer_id": reviewer_id,
        "claim_id": resolved_claim_id,
        "source_snapshot_sha256": source_snapshot_sha256,
        "source_retrieved_at": source_retrieved_at,
        "source_archive_url": source_archive_url,
        "source_snapshot_content_type": source_snapshot_content_type,
        "source_snapshot_bytes": source_snapshot_bytes,
        "source_snapshot_signature": source_snapshot_signature,
        "source_snapshot_key_id": source_snapshot_key_id,
        "source_verified": source_verified,
        "claim_review_status": claim_review_status,
        "claim_review_reviewer_id": claim_review_reviewer_id,
        "claim_reviewed_at": claim_reviewed_at,
        "claim_review_product_name": claim_review_product_name,
        "claim_review_product_url": claim_review_product_url,
        "claim_support_excerpt": claim_support_excerpt,
        "claim_review_signature": claim_review_signature,
        "claim_review_key_id": claim_review_key_id,
        "claim_review_verified": claim_review_verified,
    }, None


def _report_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _evidence_strength(item: dict[str, Any]) -> tuple[float, int, float]:
    return (
        SOURCE_WEIGHTS[item["source_type"]] * item["confidence"],
        1 if item["source_verified"] else 0,
        abs(item["impact"]),
    )


def _deduplicate_evidence(
    evidence: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Keep the strongest record for the same claim/criterion.

    Auditors can supply explicit claim_id values to tie paraphrases or derived
    sources to one underlying claim. Without claim_id, an exact normalized
    finding fingerprint is used.
    """

    kept: dict[tuple[str, str, str], dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []

    for item in evidence:
        key = (item["dimension"], item["criterion"], item["claim_id"])
        current = kept.get(key)
        if current is None:
            kept[key] = item
            continue

        if _evidence_strength(item) > _evidence_strength(current):
            dropped = current
            kept[key] = item
            retained = item
        else:
            dropped = item
            retained = current

        duplicates.append(
            {
                "dimension": item["dimension"],
                "criterion": item["criterion"],
                "claim_id": item["claim_id"],
                "dropped_source": dropped["source"],
                "retained_source": retained["source"],
                "reason": "duplicate or derived statement of the same claim",
            }
        )

    ordered = sorted(
        kept.values(),
        key=lambda x: (
            x["dimension"],
            x["criterion"],
            x["claim_id"],
            x["source"],
            x["finding"],
        ),
    )
    return ordered, duplicates


def _detect_contradictions(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_criterion: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in evidence:
        by_criterion[(item["dimension"], item["criterion"])].append(item)

    contradictions: list[dict[str, Any]] = []
    for (dimension, criterion), items in by_criterion.items():
        positive = [item for item in items if item["impact"] > 0]
        negative = [item for item in items if item["impact"] < 0]
        if positive and negative:
            contradictions.append(
                {
                    "dimension": dimension,
                    "criterion": criterion,
                    "positive_claim_ids": sorted({item["claim_id"] for item in positive}),
                    "negative_claim_ids": sorted({item["claim_id"] for item in negative}),
                    "status": "unresolved",
                }
            )
    return contradictions


def _evidence_badge_svg(
    product_name: str,
    score: int | None,
    report_hash: str,
    eligible: bool,
) -> str:
    safe_name = html.escape(product_name[:40], quote=True)
    safe_hash = html.escape(report_hash[:10], quote=True)

    if score is None:
        fill = "#4b5563"
        score_text = "UNSCORED · INSUFFICIENT EVIDENCE"
    else:
        color, band = badge_band(score)
        fill = {"green": "#15803d", "yellow": "#a16207", "red": "#b91c1c"}[color]
        status = "EVIDENCE-BACKED" if eligible else "PROVISIONAL"
        score_text = f"{score}/100 {band} · {status}"

    safe_score_text = html.escape(score_text, quote=True)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="440" height="56" role="img" '
        'aria-label="Humanity Score badge">'
        f'<rect width="440" height="56" rx="8" fill="{fill}"/>'
        f'<text x="14" y="22" font-family="Arial,sans-serif" font-size="13" fill="white">{safe_name}</text>'
        f'<text x="14" y="43" font-family="Arial,sans-serif" font-size="15" font-weight="700" fill="white">'
        f'{safe_score_text}</text>'
        f'<text x="426" y="43" font-family="monospace" font-size="9" text-anchor="end" fill="white">{safe_hash}</text>'
        '</svg>'
    )


def audit_evidence(
    *,
    product_name: str,
    description: str,
    evidence: list[dict[str, Any]],
    product_url: str = "",
    human_story: str = "",
) -> dict[str, Any]:
    """Compute an evidence-backed Humanity Score using rubric 3.0.

    Uncovered criteria are represented as None/unknown rather than receiving an
    implicit neutral 50. An overall score is produced only after evidence spans
    all three dimensions and at least six distinct criteria.

    Badge eligibility additionally requires independently retrieved source
    snapshot metadata for at least two unique source URLs.
    """

    if not isinstance(product_name, str) or not product_name.strip():
        raise ValueError("product_name is required")
    if len(product_name) > MAX_PRODUCT_NAME_CHARS:
        raise ValueError(f"product_name must not exceed {MAX_PRODUCT_NAME_CHARS} characters")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("description is required")
    if len(description) > MAX_DESCRIPTION_CHARS:
        raise ValueError(f"description must not exceed {MAX_DESCRIPTION_CHARS} characters")
    if len(human_story) > MAX_HUMAN_STORY_CHARS:
        raise ValueError(f"human_story must not exceed {MAX_HUMAN_STORY_CHARS} characters")
    if not isinstance(evidence, list):
        raise ValueError("evidence must be an array")
    if len(evidence) > MAX_EVIDENCE_ITEMS:
        raise ValueError(f"evidence must not contain more than {MAX_EVIDENCE_ITEMS} items")

    structurally_valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for index, item in enumerate(evidence):
        normalized, error = normalize_evidence(item)
        if normalized is None:
            rejected.append({"index": index, "reason": error})
        else:
            structurally_valid.append(normalized)

    valid, duplicates = _deduplicate_evidence(structurally_valid)
    contradictions = _detect_contradictions(valid)

    criterion_scores: dict[str, dict[str, int | None]] = {}
    criterion_evidence: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in valid:
        criterion_evidence[(item["dimension"], item["criterion"])].append(item)

    unknown_criteria: list[str] = []
    for dimension, criteria in DIMENSIONS.items():
        criterion_scores[dimension] = {}
        for criterion in criteria:
            items = criterion_evidence[(dimension, criterion)]
            if not items:
                criterion_scores[dimension][criterion] = None
                unknown_criteria.append(f"{dimension}.{criterion}")
                continue

            score = 50.0
            for item in items:
                weight = SOURCE_WEIGHTS[item["source_type"]]
                score += item["impact"] * 12.5 * item["confidence"] * weight
            criterion_scores[dimension][criterion] = round(clamp(score))

    dimension_scores: dict[str, int | None] = {}
    dimension_coverage: dict[str, dict[str, Any]] = {}
    for dimension, scores in criterion_scores.items():
        numeric = [score for score in scores.values() if score is not None]
        dimension_scores[dimension] = round(sum(numeric) / len(numeric)) if numeric else None
        dimension_coverage[dimension] = {
            "criteria_with_evidence": len(numeric),
            "criteria_total": len(scores),
            "coverage_ratio": round(len(numeric) / len(scores), 3),
        }

    source_urls = sorted({item["source"] for item in valid})
    source_sites = sorted({source_site(item["source"]) for item in valid if source_site(item["source"])})
    verified_source_urls = sorted({item["source"] for item in valid if item["source_verified"]})
    verified_source_sites = sorted(
        {source_site(item["source"]) for item in valid if item["source_verified"] and source_site(item["source"])}
    )
    unverified_source_urls = sorted(set(source_urls) - set(verified_source_urls))
    dimensions_covered = sorted({item["dimension"] for item in valid})
    criteria_covered = sorted({f'{item["dimension"]}.{item["criterion"]}' for item in valid})
    primary_count = sum(1 for item in valid if item["source_type"] == "primary")
    canonical_product_url = canonical_url(product_url) if product_url and valid_http_url(product_url) else ""
    reviewed_claims = [
        item
        for item in valid
        if item.get("claim_review_verified")
        and item.get("claim_review_product_name") == product_name.strip()
        and canonical_product_url
        and canonical_url(item.get("claim_review_product_url", "")) == canonical_product_url
    ]
    reviewed_criteria = sorted(
        {f'{item["dimension"]}.{item["criterion"]}' for item in reviewed_claims}
    )
    reviewed_source_sites = sorted(
        {source_site(item["source"]) for item in reviewed_claims if source_site(item["source"])}
    )

    coverage_gate = len(dimensions_covered) == 3 and len(criteria_covered) >= 6
    if coverage_gate:
        scored_dimensions = [score for score in dimension_scores.values() if score is not None]
        overall: int | None = round(sum(scored_dimensions) / len(scored_dimensions))
    else:
        overall = None

    badge_eligible = (
        overall is not None
        and bool(canonical_product_url)
        and len(valid) >= 12
        and len(source_sites) >= 6
        and len(dimensions_covered) == 3
        and len(criteria_covered) == 12
        and primary_count >= 3
        and len(verified_source_sites) >= 3
        and len(reviewed_claims) >= 12
        and len(reviewed_criteria) == 12
        and len(reviewed_source_sites) >= 3
        and not contradictions
    )

    if (
        len(valid) >= 12
        and len(source_sites) >= 6
        and len(criteria_covered) >= 9
        and primary_count >= 3
        and len(verified_source_sites) >= 3
        and not contradictions
    ):
        evidence_confidence = "high"
    elif badge_eligible:
        evidence_confidence = "moderate"
    else:
        evidence_confidence = "low"

    if contradictions and evidence_confidence == "high":
        evidence_confidence = "moderate"

    hash_payload = {
        "product_version": PRODUCT_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "product_name": product_name,
        "product_url": product_url,
        "description": description,
        "criterion_scores": criterion_scores,
        "dimension_scores": dimension_scores,
        "humanity_score": overall,
        "unknown_criteria": unknown_criteria,
        "evidence": valid,
        "contradictions": contradictions,
    }
    report_hash = _report_hash(hash_payload)

    if overall is None:
        color = "gray"
        band = "UNSCORED"
        badge_label = "UNSCORED · INSUFFICIENT EVIDENCE"
    else:
        color, band = badge_band(overall)
        badge_label = f"{band} · {'EVIDENCE-BACKED' if badge_eligible else 'PROVISIONAL'}"

    ranked = sorted(
        valid,
        key=lambda x: abs(x["impact"] * x["confidence"] * SOURCE_WEIGHTS[x["source_type"]]),
        reverse=True,
    )
    strongest_positive = next((x for x in ranked if x["impact"] > 0), None)
    strongest_concern = next((x for x in ranked if x["impact"] < 0), None)

    coverage_ratio = round(len(criteria_covered) / sum(len(v) for v in DIMENSIONS.values()), 3)

    return {
        "product_version": PRODUCT_VERSION,
        "humanity_score": overall,
        "score_status": "scored" if overall is not None else "insufficient_evidence",
        "dimension_scores": dimension_scores,
        "criterion_scores": criterion_scores,
        "criterion_coverage": dimension_coverage,
        "unknown_criteria": unknown_criteria,
        "coverage_ratio": coverage_ratio,
        "badge_color": color,
        "badge_label": badge_label,
        "badge_eligible": badge_eligible,
        "badge_svg": _evidence_badge_svg(product_name, overall, report_hash, badge_eligible),
        "assessment_mode": "evidence_backed",
        "evidence_confidence": evidence_confidence,
        "evidence_summary": {
            "submitted_findings": len(evidence),
            "structurally_valid_findings": len(structurally_valid),
            "accepted_findings": len(valid),
            "valid_findings": len(valid),
            "rejected_findings": len(rejected),
            "duplicate_findings": len(duplicates),
            "unique_sources": len(source_urls),
            "unique_source_hosts": len(source_sites),
            "verified_sources": len(verified_source_urls),
            "verified_source_hosts": len(verified_source_sites),
            "verified_findings": sum(1 for item in valid if item["source_verified"]),
            "claim_reviewed_findings": len(reviewed_claims),
            "claim_reviewed_criteria": len(reviewed_criteria),
            "claim_review_product_scope": canonical_product_url or None,
            "primary_findings": primary_count,
            "dimensions_covered": dimensions_covered,
            "criteria_covered": len(criteria_covered),
            "coverage_ratio": coverage_ratio,
            "contradictions": len(contradictions),
        },
        "source_integrity": {
            "verified_source_urls": verified_source_urls,
            "verified_source_sites": verified_source_sites,
            "unverified_source_urls": unverified_source_urls,
            "unique_source_sites": source_sites,
            "snapshot_requirement_for_badge": 3,
            "claim_review_requirement_for_badge": 12,
            "verification_rule": (
                "Only snapshots carrying a valid Humanity Score Ed25519 attestation count as "
                "independently retrieved, and EVIDENCE-BACKED badge eligibility additionally "
                "requires signed Humanity Score claim-review attestations covering all 12 criteria."
            ),
        },
        "contradictions": contradictions,
        "duplicate_evidence": duplicates,
        "strongest_positive": strongest_positive,
        "strongest_concern": strongest_concern,
        "accepted_evidence": valid,
        "source_urls": source_urls,
        "rejected_evidence": rejected,
        "report_hash": report_hash,
        "rubric_version": RUBRIC_VERSION,
        "product_name": product_name,
        "product_url": product_url,
        "description": description,
        "human_story": human_story,
        "scoring_anchors": {
            "impact": IMPACT_ANCHORS,
            "confidence": CONFIDENCE_ANCHORS,
        },
        "limitations": [
            "The score is only as strong as the evidence accepted for the audit.",
            (
                "Uncovered criteria are reported as unknown and do not receive a neutral score. "
                "An overall score is withheld until evidence covers all three dimensions and at least six criteria."
            ),
            (
                "A source URL or caller-supplied hash alone is not treated as independently verified. "
                "Badge eligibility requires valid Humanity Score Ed25519 snapshot attestations "
                "for at least three distinct source sites; subdomains of the same site do not count separately."
            ),
            (
                "A signed snapshot proves retrieval, not semantic support. EVIDENCE-BACKED badge "
                "eligibility therefore also requires signed Humanity Score claim-review attestations "
                "covering all 12 rubric criteria and bound to the audited product name and canonical product URL."
            ),
            (
                "Each claim-review attestation includes a reviewer-supplied support excerpt so the "
                "basis for the semantic judgment remains inspectable."
            ),
            (
                "A source snapshot hash proves the bytes retrieved by the audit process; without an external "
                "trusted timestamp or archive it does not independently prove when those bytes first existed."
            ),
            "Contradictory evidence is surfaced rather than silently averaged away.",
            "The Humanity Score is a product-impact rating, not a regulatory, legal, safety, or compliance certification.",
        ],
    }


def share_thread(audit: dict[str, Any]) -> list[str]:
    """Generate conservative factual share copy from an audit result."""

    name = audit["product_name"]
    score = audit["humanity_score"]
    dims = audit["dimension_scores"]
    summary = audit["evidence_summary"]
    confidence = audit["evidence_confidence"].upper()
    status = "evidence-backed" if audit["badge_eligible"] else "provisional"

    if score is None:
        return [
            f"1/ Humanity Score audit: {name} is currently UNSCORED because evidence coverage is insufficient.",
            (
                "2/ Missing evidence is not treated as neutral. "
                f"Coverage: {summary['criteria_covered']}/12 criteria across "
                f"{len(summary['dimensions_covered'])}/3 dimensions."
            ),
            (
                f"3/ Evidence confidence: {confidence}. "
                f"{summary['accepted_findings']} accepted findings across {summary['unique_sources']} source URLs."
            ),
            "4/ The audit keeps unknown criteria and contradictions visible instead of filling gaps with assumptions.",
            (
                "5/ Methodology is reproducible and source-gated. "
                f"Report hash: {audit['report_hash'][:12]}. Humanity Score is not regulatory certification."
            ),
        ]

    positive = audit.get("strongest_positive")
    concern = audit.get("strongest_concern")
    positive_text = positive["finding"] if positive else "No strong positive finding was supplied."
    concern_text = concern["finding"] if concern else "No strong negative finding was supplied."

    return [
        f"1/ Humanity Score audit: {name} scored {score}/100 ({status}).",
        (
            "2/ Dimensions — "
            f"Agency {dims['agency']}/100 · "
            f"Value Distribution {dims['value_distribution']}/100 · "
            f"Human Connection {dims['human_connection']}/100."
        ),
        (
            f"3/ Evidence confidence: {confidence}. "
            f"{summary['accepted_findings']} accepted findings across {summary['unique_sources']} source URLs; "
            f"{summary['verified_sources']} independently snapshotted."
        ),
        f"4/ Strongest positive signal: {positive_text} Strongest concern: {concern_text}",
        (
            "5/ Methodology is reproducible and source-gated. "
            f"Report hash: {audit['report_hash'][:12]}. Humanity Score is not regulatory certification."
        ),
    ]


def unverified_badge(product_name: str, score: int) -> dict[str, Any]:
    _score_inputs(score)
    report_hash = _report_hash({"product_name": product_name, "score": score, "type": "unverified"})
    color, band = badge_band(score)
    return {
        "svg": _evidence_badge_svg(product_name, score, report_hash, False),
        "score": score,
        "badge_color": color,
        "badge_label": f"{band} · UNVERIFIED",
        "verification_status": "unverified",
        "notice": "Only audit_product can issue an evidence-backed badge after evidence coverage and source-integrity gates pass.",
    }
