import unittest

from core import audit_evidence, score_self_reported, unverified_badge


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

    def test_evidence_audit_can_be_badge_eligible(self):
        result = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=GOOD_EVIDENCE,
            product_url="https://example.com",
        )
        self.assertTrue(result["badge_eligible"])
        self.assertEqual(result["evidence_confidence"], "moderate")
        self.assertEqual(result["evidence_summary"]["valid_findings"], 6)
        self.assertEqual(result["evidence_summary"]["criteria_covered"], 6)
        self.assertEqual(len(result["report_hash"]), 64)

    def test_insufficient_evidence_is_provisional(self):
        result = audit_evidence(
            product_name="Example",
            description="Example product",
            evidence=GOOD_EVIDENCE[:2],
        )
        self.assertFalse(result["badge_eligible"])
        self.assertIn("PROVISIONAL", result["badge_label"])

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

    def test_svg_escapes_product_name(self):
        result = unverified_badge('<script>alert("x")</script>', 80)
        self.assertNotIn("<script>", result["svg"])
        self.assertIn("&lt;script&gt;", result["svg"])


if __name__ == "__main__":
    unittest.main()
