"""Decision-intelligence layer for Humanity Score audits.

This module turns a scored audit into an actionable brief for founders,
buyers, and AI-governance teams without changing the underlying score.
It also compares two evidence-backed snapshots for monitoring.
"""

from __future__ import annotations

from typing import Any

from core import DIMENSIONS


CRITERION_GUIDANCE: dict[tuple[str, str], dict[str, str]] = {
    ("agency", "user_control"): {
        "action": "Document the controls users have over automation, permissions, and execution scope.",
        "question": "What can a user disable, constrain, or require approval for before the system acts?",
    },
    ("agency", "reversibility"): {
        "action": "Document rollback, deletion, export, cancellation, and recovery paths for consequential actions.",
        "question": "Which actions can be reversed, and what happens when an automated action is wrong?",
    },
    ("agency", "transparency"): {
        "action": "Expose understandable logs, explanations, provenance, and user-visible action history.",
        "question": "Can a user see what the AI did, why it did it, and which data or tools were involved?",
    },
    ("agency", "human_override"): {
        "action": "Add or document explicit human approval and escalation gates for consequential actions.",
        "question": "Where is human approval mandatory, and can a human interrupt or override execution?",
    },
    ("value_distribution", "user_benefit"): {
        "action": "Document measurable user value, pricing logic, and who receives the economic benefit created by the system.",
        "question": "What concrete benefit does the customer receive, and how is that benefit measured?",
    },
    ("value_distribution", "data_rights"): {
        "action": "Clarify ownership, training use, retention, deletion, portability, and third-party data handling.",
        "question": "Can customer data be used for training, and what deletion, export, and retention controls exist?",
    },
    ("value_distribution", "lock_in"): {
        "action": "Provide or document export, migration, interoperability, model portability, and exit paths.",
        "question": "How can a customer leave, export its data, or switch models/providers without losing essential work?",
    },
    ("value_distribution", "incentive_alignment"): {
        "action": "Document pricing and product incentives that reward useful outcomes rather than unnecessary engagement or consumption.",
        "question": "What behavior does the business model financially reward, and could that conflict with user interests?",
    },
    ("human_connection", "collaboration"): {
        "action": "Document features that support shared review, collaboration, attribution, and human-to-human work.",
        "question": "How does the product help people collaborate rather than isolate work inside an autonomous agent?",
    },
    ("human_connection", "substitution_risk"): {
        "action": "Define which human responsibilities should remain human-led and where automation is assistive rather than substitutive.",
        "question": "Which decisions or relationships should not be delegated to the AI, and how is that boundary enforced?",
    },
    ("human_connection", "social_wellbeing"): {
        "action": "Document foreseeable effects on workload, dependence, attention, trust, and user wellbeing.",
        "question": "What evidence exists about the product's effects on workload, dependence, trust, or wellbeing?",
    },
    ("human_connection", "accessibility"): {
        "action": "Document accessibility, language, disability, affordability, and inclusive-use support.",
        "question": "Who may be excluded by cost, language, disability, interface design, or required technical skill?",
    },
}


def _accepted_criteria(audit: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (item.get("dimension", ""), item.get("criterion", ""))
        for item in audit.get("accepted_evidence", [])
        if isinstance(item, dict)
    }


def _priority(score: int, covered: bool) -> tuple[int, str]:
    if score < 40:
        return 0, "critical"
    if not covered:
        return 1, "evidence_gap"
    if score < 50:
        return 2, "high"
    if score < 65:
        return 3, "medium"
    return 4, "strength"


def build_decision_intelligence(audit: dict[str, Any]) -> dict[str, Any]:
    """Turn an audit result into an actionable buyer/founder decision brief."""
    if "criterion_scores" not in audit or "dimension_scores" not in audit:
        raise ValueError("audit must be a Humanity Score evidence-backed audit result")

    covered = _accepted_criteria(audit)
    items: list[dict[str, Any]] = []

    for dimension, criteria in DIMENSIONS.items():
        dimension_scores = audit["criterion_scores"].get(dimension, {})
        for criterion in criteria:
            score = int(dimension_scores.get(criterion, 50))
            is_covered = (dimension, criterion) in covered
            order, priority = _priority(score, is_covered)
            guidance = CRITERION_GUIDANCE[(dimension, criterion)]
            items.append(
                {
                    "dimension": dimension,
                    "criterion": criterion,
                    "score": score,
                    "evidence_covered": is_covered,
                    "priority": priority,
                    "priority_order": order,
                    "recommended_action": guidance["action"],
                    "buyer_question": guidance["question"],
                }
            )

    unresolved = sorted(
        (item for item in items if item["priority"] != "strength"),
        key=lambda item: (item["priority_order"], item["score"], item["dimension"], item["criterion"]),
    )
    strengths = sorted(
        (item for item in items if item["priority"] == "strength" and item["evidence_covered"]),
        key=lambda item: (-item["score"], item["dimension"], item["criterion"]),
    )

    any_critical = any(item["score"] < 40 for item in items)
    any_missing = any(not item["evidence_covered"] for item in items)
    any_below_55 = any(item["score"] < 55 for item in items)
    confidence = audit.get("evidence_confidence", "low")

    if any_critical:
        review_signal = "deeper_review"
    elif any_missing or not audit.get("badge_eligible") or confidence == "low":
        review_signal = "evidence_review"
    elif any_below_55:
        review_signal = "targeted_review"
    else:
        review_signal = "documented_controls"

    next_review_days = 30 if review_signal in {"deeper_review", "evidence_review"} else 90

    return {
        "product_name": audit.get("product_name", ""),
        "humanity_score": audit.get("humanity_score"),
        "dimension_scores": audit.get("dimension_scores"),
        "review_signal": review_signal,
        "priority_actions": [
            {k: v for k, v in item.items() if k != "priority_order"} for item in unresolved[:6]
        ],
        "documented_strengths": [
            {k: v for k, v in item.items() if k != "priority_order"} for item in strengths[:3]
        ],
        "buyer_due_diligence_questions": [item["buyer_question"] for item in unresolved[:6]],
        "monitoring_triggers": [
            "privacy or data-retention policy changes",
            "pricing or incentive-model changes",
            "new autonomous actions or tool permissions",
            "changes to human approval or escalation controls",
            "model/provider changes that affect data use or user control",
            "material changes to export, deletion, portability, or lock-in",
        ],
        "suggested_review_interval_days": next_review_days,
        "notice": (
            "This decision brief supports product and vendor due diligence. "
            "It does not make a purchase recommendation and is not a regulatory, legal, "
            "safety, compliance, or third-party certification."
        ),
    }


def _evidence_keys(audit: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for item in audit.get("accepted_evidence", []):
        if not isinstance(item, dict):
            continue
        keys.add(
            "|".join(
                [
                    str(item.get("dimension", "")),
                    str(item.get("criterion", "")),
                    str(item.get("source", "")),
                    str(item.get("finding", "")),
                ]
            )
        )
    return keys


def compare_audit_results(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare two Humanity Score audit results for monitoring."""
    if "criterion_scores" not in previous or "criterion_scores" not in current:
        raise ValueError("previous and current must be evidence-backed Humanity Score audit results")

    dimension_deltas = {
        dimension: int(current["dimension_scores"][dimension]) - int(previous["dimension_scores"][dimension])
        for dimension in DIMENSIONS
    }

    criterion_changes: list[dict[str, Any]] = []
    for dimension, criteria in DIMENSIONS.items():
        for criterion in criteria:
            before = int(previous["criterion_scores"][dimension][criterion])
            after = int(current["criterion_scores"][dimension][criterion])
            delta = after - before
            if delta:
                criterion_changes.append(
                    {
                        "dimension": dimension,
                        "criterion": criterion,
                        "previous": before,
                        "current": after,
                        "delta": delta,
                    }
                )

    criterion_changes.sort(key=lambda item: (-abs(item["delta"]), item["dimension"], item["criterion"]))
    regressions = [item for item in criterion_changes if item["delta"] <= -5]
    improvements = [item for item in criterion_changes if item["delta"] >= 5]

    previous_evidence = _evidence_keys(previous)
    current_evidence = _evidence_keys(current)
    evidence_added = len(current_evidence - previous_evidence)
    evidence_removed = len(previous_evidence - current_evidence)
    overall_delta = int(current["humanity_score"]) - int(previous["humanity_score"])

    material_change = (
        abs(overall_delta) >= 3
        or any(abs(item["delta"]) >= 5 for item in criterion_changes)
        or evidence_added > 0
        or evidence_removed > 0
    )

    return {
        "product_name": current.get("product_name") or previous.get("product_name", ""),
        "previous_score": previous.get("humanity_score"),
        "current_score": current.get("humanity_score"),
        "overall_delta": overall_delta,
        "dimension_deltas": dimension_deltas,
        "criterion_changes": criterion_changes,
        "regressions": regressions,
        "improvements": improvements,
        "evidence_added": evidence_added,
        "evidence_removed": evidence_removed,
        "material_change": material_change,
        "current_decision_intelligence": build_decision_intelligence(current),
        "notice": (
            "A score change reflects the supplied evidence snapshots and published rubric. "
            "It does not by itself establish real-world causal impact."
        ),
    }
