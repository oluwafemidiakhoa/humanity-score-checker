import unittest

from core import audit_evidence, score_self_reported, unverified_badge
from intelligence import build_decision_intelligence, compare_audit_results
from governance import build_procurement_packet, evidence_request_checklist
from review import compare_reviewer_evidence, create_appeal_record


GOOD_EVIDENCE = [
    {
        "dimension": "agency",
        "criterion": "user_control",
        "finding": "Users can disable automated actions and choose manual control at any time.",
        "source": "https://example.com/docs/control",
        "source_type": "primary",
        "impact": 2,
        "confidence": 1.0,
    },
    {
        "dimension": "agency",
        "criterion": "reversibility",
        "finding": "The product documents deletion and export flows that let users reverse key actions.",
        "source": "https://example.com/docs/export",
        "source_type": "primary",
        "impact": 1,
        "confidence": 0.9,
    },
    {
        "dimension": "value_distribution",
        "criterion": "user_benefit",
        "finding": "Pricing documentation describes a fixed fee without advertising-based engagement incentives.",
        "source": "https://example.com/pricing",
        "source_type": "primary",
        "impact": 1,
        "confidence": 0.8,
    },
    {
        "dimension": "value_distribution",
        "criterion": "data_rights",
        "finding": "The privacy policy states that users can request deletion of stored personal data.",
        "source": "https://example.com/privacy",
        "source_type": "primary",
        "impact": 1,
        "confidence": 0.9,
    },
    {
        "dimension": "human_connection",
        "criterion": "collaboration",
        "finding": "Shared workspaces are designed for multiple people to review and revise outputs together.",
        "source": "https://example.com/docs/collaboration",
        "source_type": "primary",
        "impact": 1,
        "confidence": 0.9,
    },
    {
        "dimension": "human_connection",
        "criterion": "substitution_risk",
        "finding": "Product documentation positions automation as assistive and keeps final approval with a person.",
        "source": "https://example.com/docs/approval",
        "source_type": "secondary",
        "impact": 1,
        "confidence": 0.8,
    },
]


class HumanityScoreTests(unittest.TestCase):
    def test_self_reported_is_never_badge_eligible(self):
        result = score_self_reported(
            product_name="Example",
            description="Example product",
            agency=90,
            value_capture=90,
            connection=90,
            sources=["https://example.com/a", "https://example.com/b"],
            human_story="A sufficiently long reported user story for documentation.",
        )
        self.assertEqual(result["humanity_score"], 90)
        self.assertFalse(result["badge_eligible"])
        self.assertEqual(result["assessment_mode"], "self_reported")

    def test_score_validation_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            score_self_reported(
                product_name="Example",
                description="Example",
                agency=101,
                value_capture=50,
                connection=50,
                sources=[],
                human_story="story",
            )

    def test_evidence_audit_requires_verified_sources_for_badge(self):
        result = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=GOOD_EVIDENCE,
            product_url="https://example.com",
        )
        self.assertFalse(result["badge_eligible"])
        self.assertEqual(result["evidence_confidence"], "low")
        self.assertEqual(result["evidence_summary"]["valid_findings"], 6)
        self.assertEqual(result["evidence_summary"]["criteria_covered"], 6)
        self.assertEqual(result["evidence_summary"]["verified_sources"], 0)
        self.assertEqual(len(result["report_hash"]), 64)

    def test_verified_snapshots_can_unlock_badge(self):
        evidence = [dict(item) for item in GOOD_EVIDENCE]
        for index in (0, 1):
            evidence[index]["source_snapshot_sha256"] = ("%064x" % (index + 1))
            evidence[index]["source_retrieved_at"] = "2026-10-03T20:00:00Z"
        result = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=evidence,
            product_url="https://example.com",
        )
        self.assertTrue(result["badge_eligible"])
        self.assertEqual(result["evidence_summary"]["verified_sources"], 2)

    def test_insufficient_evidence_is_unscored_and_unknown(self):
        result = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=GOOD_EVIDENCE[:2],
        )
        self.assertFalse(result["badge_eligible"])
        self.assertIsNone(result["humanity_score"])
        self.assertEqual(result["score_status"], "insufficient_evidence")
        self.assertIn("UNSCORED", result["badge_label"])
        self.assertIsNone(result["criterion_scores"]["value_distribution"]["user_benefit"])

    def test_invalid_source_is_rejected(self):
        bad = dict(GOOD_EVIDENCE[0])
        bad["source"] = "not-a-url"
        result = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=[bad],
        )
        self.assertEqual(result["evidence_summary"]["valid_findings"], 0)
        self.assertEqual(result["evidence_summary"]["rejected_findings"], 1)

    def test_report_hash_is_deterministic(self):
        a = audit_evidence(product_name="Example", description="Example", evidence=GOOD_EVIDENCE)
        b = audit_evidence(product_name="Example", description="Example", evidence=list(reversed(GOOD_EVIDENCE)))
        self.assertEqual(a["report_hash"], b["report_hash"])

    def test_duplicate_claim_is_counted_once(self):
        evidence = [dict(item) for item in GOOD_EVIDENCE]
        duplicate = dict(evidence[0])
        duplicate["source"] = "https://example.com/duplicate"
        duplicate["claim_id"] = "same-user-control-claim"
        evidence[0]["claim_id"] = "same-user-control-claim"
        result = audit_evidence(product_name="Example", description="Example", evidence=evidence + [duplicate])
        self.assertEqual(result["evidence_summary"]["duplicate_findings"], 1)
        self.assertEqual(result["evidence_summary"]["accepted_findings"], 6)

    def test_contradiction_is_exposed(self):
        evidence = [dict(item) for item in GOOD_EVIDENCE]
        contrary = dict(evidence[0])
        contrary["finding"] = "Independent testing reports that users cannot disable automated actions after activation."
        contrary["source"] = "https://example.com/test/control"
        contrary["source_type"] = "secondary"
        contrary["impact"] = -1
        contrary["claim_id"] = "control-negative"
        evidence[0]["claim_id"] = "control-positive"
        result = audit_evidence(product_name="Example", description="Example", evidence=evidence + [contrary])
        self.assertEqual(result["evidence_summary"]["contradictions"], 1)
        self.assertEqual(result["contradictions"][0]["criterion"], "user_control")

    def test_svg_escapes_product_name(self):
        result = unverified_badge('<script>alert("x")</script>', 80)
        self.assertNotIn("<script>", result["svg"])
        self.assertIn("&lt;script&gt;", result["svg"])


    def test_reviewer_comparison_surfaces_disagreement(self):
        a = [dict(GOOD_EVIDENCE[0])]
        b = [dict(GOOD_EVIDENCE[0])]
        a[0]["claim_id"] = "control"
        b[0]["claim_id"] = "control"
        b[0]["impact"] = 1
        result = compare_reviewer_evidence(a, b)
        self.assertEqual(result["overlapping_claims"], 1)
        self.assertEqual(len(result["disagreements"]), 1)

    def test_appeal_record_is_tied_to_report(self):
        record = create_appeal_record(
            product_name="Example",
            report_hash="a" * 64,
            appellant="Example Inc.",
            claim="The published finding misstates the documented deletion control.",
            evidence_urls=["https://example.com/privacy"],
            requested_correction="Update the deletion-control finding.",
        )
        self.assertEqual(record["status"], "open")
        self.assertEqual(len(record["appeal_id"]), 20)

    def test_procurement_packet_contains_non_certifying_requests(self):
        audit = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=GOOD_EVIDENCE,
            product_url="https://example.com",
        )
        packet = build_procurement_packet(audit)
        self.assertEqual(packet["product_name"], "Example")
        self.assertTrue(packet["evidence_requests"])
        self.assertIn("does not establish compliance", packet["framework_crosswalk_notice"])

    def test_evidence_request_checklist_prioritizes_unknowns(self):
        audit = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=GOOD_EVIDENCE[:2],
        )
        requests = evidence_request_checklist(audit)
        self.assertTrue(any(item["status"] == "missing_evidence" for item in requests))

    def test_decision_intelligence_prioritizes_evidence_gaps(self):
        audit = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=GOOD_EVIDENCE,
            product_url="https://example.com",
        )
        brief = build_decision_intelligence(audit)
        self.assertEqual(brief["product_name"], "Example")
        self.assertTrue(brief["priority_actions"])
        self.assertEqual(brief["review_signal"], "evidence_review")
        self.assertTrue(brief["unknown_criteria"])
        self.assertEqual(len(brief["monitoring_triggers"]), 6)

    def test_change_monitor_detects_material_change(self):
        previous = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=GOOD_EVIDENCE,
            product_url="https://example.com",
        )
        changed = [dict(item) for item in GOOD_EVIDENCE]
        changed[0] = dict(changed[0])
        changed[0]["impact"] = -2
        current = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=changed,
            product_url="https://example.com",
        )
        diff = compare_audit_results(previous, current)
        self.assertTrue(diff["material_change"])
        self.assertLess(diff["overall_delta"], 0)
        self.assertTrue(diff["regressions"])

if __name__ == "__main__":
    unittest.main()
