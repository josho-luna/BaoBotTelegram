import unittest
from unittest.mock import MagicMock, patch

with patch.dict("sys.modules", {"genanki": MagicMock()}):
    from structure import get_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_uses_stable_target_and_explicit_translation_language(self):
        prompt = get_prompt("five colors", "ja")

        self.assertIn("Japanese flashcards", prompt)
        self.assertIn("translations in English", prompt)


if __name__ == "__main__":
    unittest.main()
