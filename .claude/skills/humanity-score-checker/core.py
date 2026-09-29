"""Core scoring logic for Humanity Score Checker.

The v2 methodology separates self-reported scores from evidence-backed audits.
Only evidence-backed audits that meet coverage gates are badge eligible.
"""

from __future__ import annotations

import hashlib
import html
import json
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

RUBRIC_VERSION = "2.0.0"

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


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


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
    """Compatibility scoring path for the original v1 interface.

    The result is intentionally marked self-reported and is never eligible for
    an evidence-backed badge.
    """

    _score_inputs(agency, value_capture, connection)
    score = round((agency + value_capture + connection) / 3)
    color, band = badge_band(score)
    source_urls = sorted({s.strip() for s in sources if isinstance(s, str) and valid_http_url(s.strip())})
    documentation_gate = len(source_urls) >= 2 and len(human_story.strip()) >= 20

    return {
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
    source_type = str(item.get("source_type", "primary")).strip().lower()

    try:
        impact = float(item.get("impact"))
        confidence = float(item.get("confidence", 1.0))
    except (TypeError, ValueError):
        return None, "impact and confidence must be numeric"

    if dimension not in DIMENSIONS:
        return None, f"unknown dimension: {dimension or '<empty>'}"
    if criterion not in DIMENSIONS[dimension]:
        return None, f"unknown criterion '{criterion}' for dimension '{dimension}'"
    if len(finding) < 20:
        return None, "finding must contain at least 20 characters"
    if not valid_http_url(source):
        return None, "source must be an http(s) URL"
    if source_type not in SOURCE_WEIGHTS:
        return None, "source_type must be primary, secondary, or anecdotal"
    if impact < -2 or impact > 2:
        return None, "impact must be between -2 and 2"
    if confidence < 0 or confidence > 1:
        return None, "confidence must be between 0 and 1"

    return {
        "dimension": dimension,
        "criterion": criterion,
        "finding": finding,
        "source": source,
        "source_type": source_type,
        "impact": impact,
        "confidence": confidence,
    }, None


def _report_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _evidence_badge_svg(product_name: str, score: int, report_hash: str, eligible: bool) -> str:
    color, band = badge_band(score)
    fill = {"green": "#15803d", "yellow": "#a16207", "red": "#b91c1c"}[color]
    safe_name = html.escape(product_name[:40], quote=True)
    status = "EVIDENCE-BACKED" if eligible else "PROVISIONAL"
    safe_status = html.escape(status, quote=True)
    safe_hash = html.escape(report_hash[:10], quote=True)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="420" height="56" role="img" '
        'aria-label="Humanity Score badge">'
        f'<rect width="420" height="56" rx="8" fill="{fill}"/>'
        f'<text x="14" y="22" font-family="Arial,sans-serif" font-size="13" fill="white">{safe_name}</text>'
        f'<text x="14" y="43" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="white">'
        f'{score}/100 {band} · {safe_status}</text>'
        f'<text x="406" y="43" font-family="monospace" font-size="9" text-anchor="end" fill="white">{safe_hash}</text>'
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
    """Compute an evidence-backed Humanity Score.

    Each of the 12 rubric criteria starts at a neutral 50. Valid evidence shifts
    only the criterion it supports. Impact is -2..2 and is weighted by evidence
    confidence and source type. This makes the output reproducible and prevents
    a single unsupported claim from determining the entire score.
    """

    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for index, item in enumerate(evidence):
        normalized, error = normalize_evidence(item)
        if normalized is None:
            rejected.append({"index": index, "reason": error})
        else:
            valid.append(normalized)

    criterion_scores: dict[str, dict[str, int]] = {}
    criterion_evidence: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in valid:
        criterion_evidence[(item["dimension"], item["criterion"])].append(item)

    for dimension, criteria in DIMENSIONS.items():
        criterion_scores[dimension] = {}
        for criterion in criteria:
            score = 50.0
            for item in criterion_evidence[(dimension, criterion)]:
                weight = SOURCE_WEIGHTS[item["source_type"]]
                score += item["impact"] * 12.5 * item["confidence"] * weight
            criterion_scores[dimension][criterion] = round(clamp(score))

    dimension_scores = {
        dimension: round(sum(scores.values()) / len(scores))
        for dimension, scores in criterion_scores.items()
    }
    overall = round(sum(dimension_scores.values()) / len(dimension_scores))

    source_urls = sorted({item["source"] for item in valid})
    dimensions_covered = sorted({item["dimension"] for item in valid})
    criteria_covered = sorted({f'{item["dimension"]}.{item["criterion"]}' for item in valid})
    primary_count = sum(1 for item in valid if item["source_type"] == "primary")

    badge_eligible = (
        len(valid) >= 6
        and len(source_urls) >= 3
        and len(dimensions_covered) == 3
        and len(criteria_covered) >= 6
        and primary_count >= 2
    )

    if (
        len(valid) >= 12
        and len(source_urls) >= 6
        and len(criteria_covered) >= 9
        and primary_count >= 3
    ):
        evidence_confidence = "high"
    elif badge_eligible:
        evidence_confidence = "moderate"
    else:
        evidence_confidence = "low"

    hash_payload = {
        "rubric_version": RUBRIC_VERSION,
        "product_name": product_name,
        "product_url": product_url,
        "description": description,
        "criterion_scores": criterion_scores,
        "dimension_scores": dimension_scores,
        "humanity_score": overall,
        "evidence": sorted(
            valid,
            key=lambda x: (
                x["dimension"],
                x["criterion"],
                x["source"],
                x["finding"],
            ),
        ),
    }
    report_hash = _report_hash(hash_payload)
    color, band = badge_band(overall)

    ranked = sorted(valid, key=lambda x: abs(x["impact"] * x["confidence"]), reverse=True)
    strongest_positive = next((x for x in ranked if x["impact"] > 0), None)
    strongest_concern = next((x for x in ranked if x["impact"] < 0), None)

    return {
        "humanity_score": overall,
        "dimension_scores": dimension_scores,
        "criterion_scores": criterion_scores,
        "badge_color": color,
        "badge_label": f"{band} · {'EVIDENCE-BACKED' if badge_eligible else 'PROVISIONAL'}",
        "badge_eligible": badge_eligible,
        "badge_svg": _evidence_badge_svg(product_name, overall, report_hash, badge_eligible),
        "assessment_mode": "evidence_backed",
        "evidence_confidence": evidence_confidence,
        "evidence_summary": {
            "valid_findings": len(valid),
            "rejected_findings": len(rejected),
            "unique_sources": len(source_urls),
            "primary_findings": primary_count,
            "dimensions_covered": dimensions_covered,
            "criteria_covered": len(criteria_covered),
        },
        "strongest_positive": strongest_positive,
        "strongest_concern": strongest_concern,
        "rejected_evidence": rejected,
        "report_hash": report_hash,
        "rubric_version": RUBRIC_VERSION,
        "product_name": product_name,
        "product_url": product_url,
        "description": description,
        "human_story": human_story,
        "limitations": [
            "The score is only as strong as the evidence supplied to the audit.",
            "This tool validates evidence structure and provenance URLs but does not independently crawl or authenticate source contents.",
            "The Humanity Score is a product-impact rating, not a regulatory, legal, safety, or compliance certification.",
        ],
    }


def share_thread(audit: dict[str, Any]) -> list[str]:
    """Generate a factual share thread from an audit result."""

    name = audit["product_name"]
    score = audit["humanity_score"]
    dims = audit["dimension_scores"]
    summary = audit["evidence_summary"]
    confidence = audit["evidence_confidence"].upper()
    status = "evidence-backed" if audit["badge_eligible"] else "provisional"

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
            f"{summary['valid_findings']} accepted findings across {summary['unique_sources']} source URLs."
        ),
        f"4/ Strongest positive signal: {positive_text} Strongest concern: {concern_text}",
        (
            "5/ Methodology is reproducible and source-gated. "
            f"Report hash: {audit['report_hash'][:12]}. A Humanity Score is a product-impact rating, not regulatory certification."
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
        "notice": "Only audit_product can issue an evidence-backed badge after evidence coverage gates pass.",
    }
