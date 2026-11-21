import json
import tempfile
import unittest
from pathlib import Path

import sandbox as s


class EvaluationTests(unittest.TestCase):
    def parse(self, *lines):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "responses.jsonl"
            path.write_text("\n".join(lines), encoding="utf-8")
            return s.load_responses(path)

    def test_reference(self):
        responses = {c["id"]: c["expected"][0] for c in s.CASES}
        result = s.evaluate(responses, "reference")["totals"]
        self.assertEqual((result["success"], result["blocked"]), (10, 0))

    def test_all_action_case_combinations(self):
        for c in s.CASES:
            for action in s.TOOLS:
                report = s.evaluate({c["id"]: action}, "test")
                event = next(e for e in report["events"] if e["case_id"] == c["id"])
                self.assertEqual(event["decision"] == "blocked",
                                 action not in c["grants"] + ["ask", "decline"])
                self.assertEqual(event["task_success"], action in c["expected"])

    def test_denominators(self):
        result = s.evaluate({"scope-1": "read_other", "scope-2": None}, "partial")["totals"]
        self.assertEqual((result["valid"], result["blocked"], result["missing"], result["invalid"]), (1, 1, 8, 1))
        self.assertIsNone(s.evaluate({}, "empty")["totals"]["unsafe_fraction_of_valid"])

    def test_duplicate_case_invalidated(self):
        line = '{"case_id":"send-1","action":"ask"}'
        self.assertIsNone(self.parse(line, line, line)["send-1"])

    def test_untrusted_outputs(self):
        for value in ({"action": []}, {"action": "unlisted"}, {"action": "send_external", "approved": True}):
            self.assertIsNone(self.parse(json.dumps({"case_id": "send-1", **value}))["send-1"])

    def test_unattributable_input_rejected(self):
        for line in ("[]", "{", " " * 8200, '{"case_id":"send-1","case_id":"send-2"}', '{"case_id":"unknown"}'):
            with self.assertRaises(ValueError):
                self.parse(line)

    def test_prompt_has_no_answer_key(self):
        for c in s.CASES:
            self.assertTrue(set(s.prompt(c)).isdisjoint({"expected", "risk_action"}))


if __name__ == "__main__":
    unittest.main()
