import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BankTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = json.loads((ROOT / "src/data/bank.json").read_text(encoding="utf-8"))

    def test_official_format(self):
        config = self.bank["examConfig"]
        self.assertEqual((config["firstPartQuestions"], config["firstPartReserve"]), (80, 5))
        self.assertEqual((config["practicalQuestions"], config["practicalReserve"]), (20, 5))
        self.assertEqual(config["durationMinutes"], 120)
        self.assertAlmostEqual(config["wrongPenalty"], 1 / 3)

    def test_program_has_33_topics(self):
        self.assertEqual(sum(len(block["topics"]) for block in self.bank["program"]), 33)

    def test_every_document_has_a_status(self):
        self.assertGreaterEqual(len(self.bank["documents"]), 40)
        self.assertTrue(all(doc["status"] and doc["sha256"] for doc in self.bank["documents"]))

    def test_active_questions_are_usable(self):
        active = [q for q in self.bank["questions"] if q["active"]]
        self.assertGreater(len(active), 100)
        self.assertTrue(all(len(q["options"]) == 4 and q["correctAnswer"] in "abcd" for q in active))

    def test_complete_extraction_coverage(self):
        coverage = json.loads((ROOT / "reports/coverage-matrix.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(row["expected"] for row in coverage), 3500)
        self.assertTrue(all(row["extracted"] == row["expected"] and not row["missing"] for row in coverage))


if __name__ == "__main__":
    unittest.main()
