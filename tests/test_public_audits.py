import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDITS = ROOT / "public_audits"


class PublicAuditConsistencyTests(unittest.TestCase):
    def test_markdown_metadata_matches_canonical_json(self):
        for directory in sorted(p for p in AUDITS.iterdir() if p.is_dir()):
            json_path = directory / "preliminary.json"
            md_path = directory / "README.md"
            if not json_path.exists() or not md_path.exists():
                continue

            data = json.loads(json_path.read_text(encoding="utf-8"))
            md = md_path.read_text(encoding="utf-8")

            with self.subTest(audit=directory.name):
                score_match = re.search(r"\*\*Humanity Score:\*\* \*\*(\d+)/100\*\*", md)
                hash_match = re.search(r"\*\*Report hash:\*\* `([0-9a-f]{64})`", md)
                self.assertIsNotNone(score_match)
                self.assertIsNotNone(hash_match)
                self.assertEqual(int(score_match.group(1)), data["humanity_score"])
                self.assertEqual(hash_match.group(1), data["report_hash"])

                for label, key in (
                    ("Agency", "agency"),
                    ("Value Distribution", "value_distribution"),
                    ("Human Connection", "human_connection"),
                ):
                    match = re.search(rf"- {re.escape(label)}: \*\*(\d+)/100\*\*", md)
                    self.assertIsNotNone(match)
                    self.assertEqual(int(match.group(1)), data["dimension_scores"][key])


if __name__ == "__main__":
    unittest.main()
