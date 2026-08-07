import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


def load_structure_module():
    module_path = Path(__file__).resolve().parents[1] / "structure.py"
    spec = importlib.util.spec_from_file_location("_structure_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"genanki": MagicMock(), spec.name: module}):
        spec.loader.exec_module(module)
    return module


structure = load_structure_module()


class PromptTests(unittest.TestCase):
    def test_prompt_uses_stable_target_and_explicit_translation_language(self):
        prompt = structure.get_prompt("five colors", "ja")

        self.assertIn("Japanese flashcards", prompt)
        self.assertIn("translations in English", prompt)

    def test_every_supported_language_has_specific_pronunciation_guidance(self):
        expected_guidance = {
            "zh": "Hanyu Pinyin with tone marks",
            "ja": "kana reading",
            "ko": "phonetic Hangul",
            "es": "broad IPA",
            "ar": "fully vowelled Arabic",
            "fr": "broad IPA",
            "de": "broad IPA",
        }

        self.assertEqual(set(expected_guidance), set(structure.TARGET_LANGUAGES))
        for language, guidance in expected_guidance.items():
            with self.subTest(language=language):
                prompt = structure.get_prompt("one useful word", language)
                self.assertIn(guidance, prompt)
                self.assertIn("return exactly an empty string", prompt)
                self.assertIn("short, natural", prompt)

    def test_pinyin_is_chinese_only_and_japanese_never_requests_romaji(self):
        chinese_prompt = structure.get_prompt("water", "zh")
        japanese_prompt = structure.get_prompt("water", "ja")

        self.assertIn("Pinyin", chinese_prompt)
        self.assertNotIn("Pinyin", japanese_prompt)
        self.assertIn("never use Romaji", japanese_prompt)

    def test_request_is_json_encoded_without_losing_unicode(self):
        prompt = structure.get_prompt('café\n"please"', "fr")

        self.assertIn('Learner request: "café\\n\\"please\\""', prompt)

    def test_unsupported_language_is_not_silently_treated_as_chinese(self):
        with self.assertRaisesRegex(ValueError, "Unsupported target language"):
            structure.get_prompt("hello", "xx")


class SchemaTests(unittest.TestCase):
    def test_structured_output_uses_generic_multilingual_fields(self):
        self.assertEqual(
            list(structure.FlashcardFields.__annotations__),
            [
                "word",
                "pronunciation",
                "definition",
                "notes",
                "example_sentence",
                "example_pronunciation",
                "example_translation",
            ],
        )

    def test_anki_model_fields_match_deck_contract(self):
        structure.genanki.Model.reset_mock()
        structure.ankigen()
        _, kwargs = structure.genanki.Model.call_args

        self.assertEqual(
            [field["name"] for field in kwargs["fields"]],
            [
                "Word",
                "Pronunciation",
                "Definition",
                "Notes",
                "Sentence",
                "SentencePronunciation",
                "SentenceTranslation",
                "WordAudio",
                "SentenceAudio",
                "Language",
                "Locale",
                "LanguageName",
            ],
        )
        self.assertEqual(structure.genanki.Model.call_args.args[1], "BaoCards Multilingual v2")

    def test_templates_hide_empty_optional_fields_and_select_language_style(self):
        self.assertIn("language-{{Language}}", structure.ANSWER)
        self.assertIn("{{#Word}}", structure.TARGET_FRONT)
        self.assertIn("{{#Definition}}", structure.DEFINITION_FRONT)
        self.assertIn("{{LanguageName}}", structure.DEFINITION_FRONT)
        self.assertIn('lang="{{Locale}}"', structure.ANSWER)
        self.assertIn("{{#Pronunciation}}", structure.ANSWER)
        self.assertIn("{{#Notes}}", structure.ANSWER)
        self.assertIn("{{#SentencePronunciation}}", structure.ANSWER)
        self.assertNotIn("blur-guard", structure.ANSWER)

    def test_css_has_offline_script_specific_fonts_and_rtl_support(self):
        for language in structure.TARGET_LANGUAGES:
            with self.subTest(language=language):
                self.assertIn(f".language-{language}", structure.CSS)

        self.assertIn('"Kaiti SC"', structure.CSS)
        self.assertIn('"Noto Sans CJK JP"', structure.CSS)
        self.assertIn('"Noto Sans CJK KR"', structure.CSS)
        self.assertIn('"Noto Naskh Arabic"', structure.CSS)
        self.assertIn(".language-ar .target-text", structure.CSS)
        self.assertIn("direction: rtl", structure.CSS)
        self.assertIn("clamp(", structure.CSS)
        self.assertNotIn("@import", structure.CSS)
        self.assertNotIn("AdobeKaiti", structure.CSS)


if __name__ == "__main__":
    unittest.main()
