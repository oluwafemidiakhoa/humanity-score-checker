import unittest

from provenance import validate_public_url


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


if __name__ == "__main__":
    unittest.main()
