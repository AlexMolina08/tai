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
        self.assertEqual(sum(row["expected"] for row in coverage), 3520)
        self.assertTrue(all(row["extracted"] == row["expected"] and not row["missing"] for row in coverage))

    def test_supplemental_topic_9_questions_are_merged_once(self):
        source = json.loads((ROOT / "sources/test_t9_examenes.json").read_text(encoding="utf-8"))
        by_id = {question["id"]: question for question in self.bank["questions"]}
        for item in source["questions"]:
            question_id = item["existingId"] or f"{source['meta']['id']}:first:{item['sourceNumber']}"
            question = by_id[question_id]
            self.assertEqual(question["topicId"], "I.9")
            self.assertEqual(question["prompt"], item["prompt"])
            self.assertEqual(question["options"], item["options"])
            self.assertEqual(question["correctAnswer"], item["correctAnswer"])
            self.assertEqual(question["active"], item["active"])
        self.assertEqual(source["meta"]["internalDuplicates"], {"33": 8, "34": 10})


if __name__ == "__main__":
    unittest.main()
