import tempfile
import unittest
from pathlib import Path

from audit_receipt import build_public_receipt, receipt_html, write_receipt_bundle
from core import audit_evidence
from tests.test_core import GOOD_EVIDENCE


class PublicReceiptTests(unittest.TestCase):
    def setUp(self):
        self.audit = audit_evidence(
            product_name="Example AI",
            description="Example AI product",
            evidence=GOOD_EVIDENCE,
            product_url="https://example.com",
        )

    def test_receipt_contains_verification_fields(self):
        receipt = build_public_receipt(self.audit, audit_date="2026-10-01")
        self.assertEqual(receipt["schema"], "humanity-score.public-audit-receipt.v1")
        self.assertEqual(receipt["report_hash"], self.audit["report_hash"])
        self.assertEqual(receipt["audit_date"], "2026-10-01")
        self.assertEqual(len(receipt["accepted_evidence"]), 6)

    def test_html_escapes_product_name(self):
        audit = dict(self.audit)
        audit["product_name"] = "<script>alert(1)</script>"
        receipt = build_public_receipt(audit, audit_date="2026-10-01")
        rendered = receipt_html(receipt)
        self.assertNotIn("<script>alert(1)</script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_bundle_writes_json_markdown_and_html(self):
        receipt = build_public_receipt(self.audit, audit_date="2026-10-01")
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_receipt_bundle(receipt, tmp)
            for value in paths.values():
                self.assertTrue(Path(value).exists())


if __name__ == "__main__":
    unittest.main()
