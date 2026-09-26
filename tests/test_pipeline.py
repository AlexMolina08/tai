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

    def test_bank_is_empty(self):
        self.assertEqual(self.bank["documents"], [])
        self.assertEqual(self.bank["exams"], [])
        self.assertEqual(self.bank["questions"], [])



if __name__ == "__main__":
    unittest.main()
