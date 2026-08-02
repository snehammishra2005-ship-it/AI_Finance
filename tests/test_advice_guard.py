import unittest

from backend.services.llm_service import advice_safety_note


class AdviceSafetyNote(unittest.TestCase):
    def test_triggers_on_bare_no_to_personal_question(self):
        note = advice_safety_note("Should I put all my savings into Tesla stock?", "No.")
        self.assertIsNotNone(note)
        self.assertIn("licensed financial advisor", note)

    def test_triggers_on_bare_yes(self):
        self.assertIsNotNone(advice_safety_note("Should I go all in on crypto?", "Yes"))

    def test_triggers_with_markdown_wrapping(self):
        self.assertIsNotNone(advice_safety_note("Should I invest everything now?", "**No.**"))

    def test_not_triggered_when_answer_is_substantive(self):
        answer = ("It depends on your goals. Concentrating in one stock is risky; "
                  "diversifying and consulting an advisor is wise.")
        self.assertIsNone(advice_safety_note("Should I buy Tesla?", answer))

    def test_not_triggered_on_factual_question(self):
        # A general factual question that happens to get a short answer must
        # NOT be rewritten.
        self.assertIsNone(advice_safety_note("Is inflation currently high?", "No."))

    def test_not_triggered_on_definition_question(self):
        self.assertIsNone(advice_safety_note("What does APR stand for?", "Annual Percentage Rate."))

    def test_empty_inputs_return_none(self):
        self.assertIsNone(advice_safety_note("", "No."))
        self.assertIsNone(advice_safety_note("Should I buy?", ""))


if __name__ == "__main__":
    unittest.main()
