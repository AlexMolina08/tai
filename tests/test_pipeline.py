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

    def test_bank_integrity(self):
        self.assertEqual(len(self.bank["exams"]), 5)
        self.assertEqual(len(self.bank["questions"]), 675)
        self.assertTrue(len(self.bank["documents"]) >= 10)
        for q in self.bank["questions"]:
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["correctAnswer"], ["a", "b", "c", "d", "anulada", None])



if __name__ == "__main__":
    unittest.main()
