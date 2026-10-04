import json
import os
import unittest

from provenance import sign_document, validate_public_url, verify_document_signature


class ProvenanceSafetyTests(unittest.TestCase):
    def test_rejects_localhost(self):
        with self.assertRaises(ValueError):
            validate_public_url("http://localhost/admin")

    def test_rejects_loopback_ip(self):
        with self.assertRaises(ValueError):
            validate_public_url("http://127.0.0.1/secret")

    def test_rejects_url_credentials(self):
        with self.assertRaises(ValueError):
            validate_public_url("https://user:pass@example.com/private")

    def test_rejects_shared_address_space(self):
        with self.assertRaises(ValueError):
            validate_public_url("http://100.64.0.1/internal")

    def test_historical_public_key_can_verify_after_rotation(self):
        old_private = os.environ.get("HUMANITY_SCORE_SIGNING_KEY")
        old_trusted = os.environ.get("HUMANITY_SCORE_TRUSTED_PUBLIC_KEYS_JSON")
        try:
            os.environ["HUMANITY_SCORE_SIGNING_KEY"] = "11" * 32
            payload = {"example": "receipt"}
            signed = sign_document(payload, purpose="audit_receipt")
            old_key_id = signed["signing_key_id"]
            old_public_key = signed["signing_public_key"]

            os.environ["HUMANITY_SCORE_SIGNING_KEY"] = "22" * 32
            os.environ["HUMANITY_SCORE_TRUSTED_PUBLIC_KEYS_JSON"] = json.dumps(
                {old_key_id: old_public_key}
            )
            self.assertTrue(
                verify_document_signature(
                    payload,
                    purpose="audit_receipt",
                    signature=signed["signature"],
                    signing_key_id=old_key_id,
                )
            )
        finally:
            if old_private is None:
                os.environ.pop("HUMANITY_SCORE_SIGNING_KEY", None)
            else:
                os.environ["HUMANITY_SCORE_SIGNING_KEY"] = old_private
            if old_trusted is None:
                os.environ.pop("HUMANITY_SCORE_TRUSTED_PUBLIC_KEYS_JSON", None)
            else:
                os.environ["HUMANITY_SCORE_TRUSTED_PUBLIC_KEYS_JSON"] = old_trusted


if __name__ == "__main__":
    unittest.main()
