"""Procurement and governance interoperability helpers for Humanity Score.

These outputs are explicitly non-certifying. They package Humanity Score
evidence into questions and mappings that enterprise governance teams can use
alongside their own legal, security, privacy, safety, and compliance processes.
"""

from __future__ import annotations

from typing import Any

from core import DIMENSIONS
from intelligence import CRITERION_GUIDANCE


FRAMEWORK_THEME_MAP: dict[tuple[str, str], list[str]] = {
    ("agency", "user_control"): [
        "NIST AI RMF: Govern / Manage — roles, controls, intervention",
        "ISO/IEC 42001: operational controls and human oversight themes",
        "EU AI Act: human oversight / user control themes where applicable",
    ],
    ("agency", "reversibility"): [
        "NIST AI RMF: Manage — response, recovery, lifecycle controls",
        "ISO/IEC 42001: operational change and incident-management themes",
    ],
    ("agency", "transparency"): [
        "NIST AI RMF: Map / Measure — documentation and transparency",
        "ISO/IEC 42001: documented information and traceability themes",
        "EU AI Act: transparency/documentation themes where applicable",
    ],
    ("agency", "human_override"): [
        "NIST AI RMF: Govern / Manage — accountability and intervention",
        "EU AI Act: human oversight themes where applicable",
    ],
    ("value_distribution", "user_benefit"): [
        "NIST AI RMF: Map — intended purpose, affected stakeholders, impacts",
        "ISO/IEC 42001: objectives, impact assessment, stakeholder considerations",
    ],
    ("value_distribution", "data_rights"): [
        "NIST AI RMF: Map / Manage — data governance and privacy risk",
        "ISO/IEC 42001: data/resource governance themes",
    ],
    ("value_distribution", "lock_in"): [
        "Third-party/vendor risk and operational resilience themes",
        "Portability, exit planning, and dependency-management themes",
    ],
    ("value_distribution", "incentive_alignment"): [
        "NIST AI RMF: Govern — accountability and risk culture",
        "Organizational incentives and conflict-of-interest themes",
    ],
    ("human_connection", "collaboration"): [
        "NIST AI RMF: human factors and socio-technical context themes",
        "Organizational role and human-review themes",
    ],
    ("human_connection", "substitution_risk"): [
        "NIST AI RMF: Map — human/AI role allocation and affected stakeholders",
        "EU AI Act: human oversight themes where applicable",
    ],
    ("human_connection", "social_wellbeing"): [
        "NIST AI RMF: Map / Measure — impacts on people and communities",
        "Societal and human-factor impact-monitoring themes",
    ],
    ("human_connection", "accessibility"): [
        "Accessibility, inclusion, and affected-person considerations",
        "NIST AI RMF: Map — impacted individuals and communities",
    ],
}


def evidence_request_checklist(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a vendor evidence request list from unknown/weak criteria."""

    covered = {
        (item.get("dimension"), item.get("criterion"))
        for item in audit.get("accepted_evidence", [])
        if isinstance(item, dict)
    }
    rows: list[dict[str, Any]] = []

    for dimension, criteria in DIMENSIONS.items():
        scores = audit.get("criterion_scores", {}).get(dimension, {})
        for criterion in criteria:
            score = scores.get(criterion)
            missing = (dimension, criterion) not in covered or score is None
            if not missing and isinstance(score, int) and score >= 65:
                continue

            guidance = CRITERION_GUIDANCE[(dimension, criterion)]
            rows.append(
                {
                    "dimension": dimension,
                    "criterion": criterion,
                    "current_score": score,
                    "status": "missing_evidence" if missing else "follow_up",
                    "request": guidance["question"],
                    "preferred_evidence": [
                        "product documentation or control description",
                        "policy/terms/privacy documentation where relevant",
                        "independent testing or customer evidence where available",
                        "dated source snapshot or preserved document",
                    ],
                    "framework_themes": FRAMEWORK_THEME_MAP[(dimension, criterion)],
                }
            )
    return rows


def build_procurement_packet(audit: dict[str, Any]) -> dict[str, Any]:
    """Package an audit for procurement/governance intake without certifying it."""

    return {
        "schema": "humanity-score.procurement-packet.v1",
        "product_name": audit.get("product_name", ""),
        "product_url": audit.get("product_url", ""),
        "report_hash": audit.get("report_hash", ""),
        "rubric_version": audit.get("rubric_version", ""),
        "score_status": audit.get("score_status", "scored"),
        "humanity_score": audit.get("humanity_score"),
        "dimension_scores": audit.get("dimension_scores", {}),
        "coverage_ratio": audit.get("coverage_ratio"),
        "evidence_confidence": audit.get("evidence_confidence"),
        "source_integrity": audit.get("source_integrity", {}),
        "unknown_criteria": audit.get("unknown_criteria", []),
        "contradictions": audit.get("contradictions", []),
        "evidence_requests": evidence_request_checklist(audit),
        "monitoring_triggers": [
            "privacy, retention, or training-use policy changes",
            "pricing or incentive-model changes",
            "new autonomous actions, tool permissions, or agent capabilities",
            "changes to human approval, override, or escalation controls",
            "model/provider changes affecting data use, security, or user control",
            "material changes to export, deletion, portability, or lock-in",
        ],
        "framework_crosswalk_notice": (
            "Framework themes are decision-support mappings only. This packet does not "
            "establish compliance or conformity with NIST AI RMF, ISO/IEC 42001, the EU AI Act, "
            "or any other legal/regulatory framework."
        ),
        "scope_notice": (
            "Humanity Score is one due-diligence evidence layer. Procurement should combine it "
            "with security, privacy, legal, model validation, safety, and formal compliance review "
            "as applicable."
        ),
    }
