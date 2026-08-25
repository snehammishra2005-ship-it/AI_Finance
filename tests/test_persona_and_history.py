import re
import unittest

from utils.persona_manager import load_personas, get_persona_names, get_persona_prompt
from backend.services.history_service import derive_title


class PersonaManager(unittest.TestCase):
    def test_loads_all_personas_from_prompts_file(self):
        names = get_persona_names()
        self.assertIn("Student Persona", names)
        self.assertIn("General User Persona", names)
        self.assertGreaterEqual(len(names), 5)

    def test_known_persona_has_nonempty_prompt(self):
        self.assertTrue(get_persona_prompt("Student Persona").strip())

    def test_unknown_persona_falls_back_to_default_string(self):
        prompt = get_persona_prompt("Definitely Not A Persona")
        self.assertIn("financial insights", prompt.lower())

    def test_missing_file_returns_general_user_default(self):
        personas = load_personas(file_path="/no/such/file.md")
        self.assertIn("General User", personas)


class DeriveTitle(unittest.TestCase):
    def test_uses_first_user_message(self):
        messages = [
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "What is inflation?"},
        ]
        self.assertEqual(derive_title(messages), "What is inflation?")

    def test_long_message_is_truncated_with_ellipsis(self):
        long = "Explain the entire history of central banking in great detail please"
        title = derive_title([{"role": "user", "content": long}])
        self.assertTrue(title.endswith("…"))
        self.assertLessEqual(len(title), 39)  # 38 chars + ellipsis

    def test_collapses_whitespace(self):
        messages = [{"role": "user", "content": "hello    there\n\nworld"}]
        self.assertEqual(derive_title(messages), "hello there world")

    def test_falls_back_to_timestamp_without_user_message(self):
        title = derive_title([{"role": "assistant", "content": "Hi"}])
        self.assertRegex(title, r"^\d{8}_\d{6}$")

    def test_empty_messages_falls_back_to_timestamp(self):
        self.assertRegex(derive_title([]), r"^\d{8}_\d{6}$")


if __name__ == "__main__":
    unittest.main()
