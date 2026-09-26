import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ManualClassificationTest(unittest.TestCase):
    def test_all_reviewed_questions_survive_reimport(self):
        bank = json.loads((ROOT / 'src/data/bank.json').read_text())
        decisions = json.loads((ROOT / 'src/data/manual-classifications.json').read_text())
        questions = {q['id']: q for q in bank['questions']}

        self.assertEqual(len(decisions), 102)
        self.assertEqual(sum(q['status'] == 'classification_review' for q in questions.values()), 0)
        for question_id, decision in decisions.items():
            question = questions[question_id]
            with self.subTest(question_id=question_id):
                self.assertEqual(question['topicId'], decision['topicId'])
                self.assertEqual(question['blockId'], decision['topicId'].split('.')[0])
                self.assertEqual(question['classificationMethod'], 'revision_manual_2026_09_26')
                self.assertTrue(decision['reason'])


if __name__ == '__main__':
    unittest.main()
