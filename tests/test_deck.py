import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


fake_genanki = MagicMock()
fake_google = types.ModuleType("google")
fake_google.genai = MagicMock()
fake_audio = types.ModuleType("audio")
fake_audio.generate_audio = AsyncMock()
fake_structure = types.ModuleType("structure")
fake_structure.ankigen = MagicMock()
fake_structure.FlashcardList = MagicMock()


def load_deck_module():
    module_path = Path(__file__).resolve().parents[1] / "deck.py"
    spec = importlib.util.spec_from_file_location("_deck_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    dependencies = {
        "genanki": fake_genanki,
        "google": fake_google,
        "google.genai": fake_google.genai,
        "audio": fake_audio,
        "structure": fake_structure,
        spec.name: module,
    }
    with patch.dict(sys.modules, dependencies):
        spec.loader.exec_module(module)
    return module


deck = load_deck_module()


def card(**overrides):
    values = {
        "word": "Wort",
        "pronunciation": "",
        "definition": "word",
        "notes": "die Wörter",
        "example_sentence": "Das ist ein Wort.",
        "example_pronunciation": "",
        "example_translation": "That is a word.",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class DeckFormattingTests(unittest.TestCase):
    def test_summary_omits_empty_pronunciation_parentheses(self):
        self.assertEqual(deck._format_summary([card()]), "✅ Wort")
        self.assertEqual(deck._format_summary([card(pronunciation="  ")]), "✅ Wort")
        self.assertEqual(
            deck._format_summary([card(pronunciation="vɔʁt")]),
            "✅ Wort (vɔʁt)",
        )

    def test_summary_reports_truncated_card_count(self):
        cards = [card(word=f"word {index}") for index in range(10)]

        summary = deck._format_summary(cards)

        self.assertEqual(len(summary.splitlines()), 9)
        self.assertTrue(summary.endswith("+2"))

    def test_note_fields_follow_model_order_and_escape_plain_text(self):
        fields = deck._note_fields(
            card(word="<Wort>", notes="A & B"),
            "word.mp3",
            "sentence.mp3",
            "de",
        )

        self.assertEqual(
            fields,
            [
                "&lt;Wort&gt;",
                "",
                "word",
                "A &amp; B",
                "Das ist ein Wort.",
                "",
                "That is a word.",
                "[sound:word.mp3]",
                "[sound:sentence.mp3]",
                "de",
                "de-DE",
                "German",
            ],
        )

    def test_audio_uses_disambiguating_script_readings_but_not_ipa(self):
        arabic = card(
            word="كتب",
            pronunciation="كَتَبَ",
            example_sentence="كتب رسالة.",
            example_pronunciation="كَتَبَ رِسَالَةً.",
        )
        french = card(word="chat", pronunciation="ʃa")

        self.assertEqual(
            deck._audio_text(arabic, "ar"),
            ("كَتَبَ", "كَتَبَ رِسَالَةً."),
        )
        self.assertEqual(deck._audio_text(french, "fr"), ("chat", "Das ist ein Wort."))

    def test_card_validation_respects_language_pronunciation_policy(self):
        self.assertTrue(deck._is_usable_card(card(), "de"))
        self.assertFalse(deck._is_usable_card(card(word="  "), "de"))
        self.assertFalse(deck._is_usable_card(card(), "zh"))
        self.assertTrue(
            deck._is_usable_card(
                card(pronunciation="shuǐ", example_pronunciation="zhè shì yí ge cí."),
                "zh",
            )
        )


class DeckGenerationTests(unittest.TestCase):
    def test_generation_rejects_unknown_language_before_api_call(self):
        with self.assertRaisesRegex(ValueError, "Unsupported target language"):
            deck.generate_anki_deck("prompt", "xx", "key", "voice", "edge", None)

    def test_generation_maps_schema_to_model_and_package(self):
        generated_card = card(word="das Wort", pronunciation="")
        response = SimpleNamespace(parsed=SimpleNamespace(cards=[generated_card]))
        client = MagicMock()
        client.models.generate_content.return_value = response
        note_model = object()
        anki_deck = MagicMock()
        package = MagicMock()

        def validate_note(*, model, fields):
            self.assertIs(model, note_model)
            self.assertEqual(len(fields), 12)
            self.assertEqual(fields[-3:], ["de", "de-DE", "German"])
            return SimpleNamespace(model=model, fields=fields)

        with tempfile.TemporaryDirectory() as temp_dir:
            package.write_to_file.side_effect = lambda path: Path(path).touch()
            with (
                patch.object(deck, "TEMP_DIR", temp_dir),
                patch.object(deck.genai, "Client", return_value=client),
                patch.object(deck, "ankigen", return_value=note_model),
                patch.object(deck.genanki, "Deck", return_value=anki_deck),
                patch.object(deck.genanki, "Note", side_effect=validate_note),
                patch.object(deck.genanki, "Package", return_value=package),
                patch.object(deck, "generate_audio", new_callable=AsyncMock) as audio_mock,
            ):
                apkg_path, summary, count, media_files = deck.generate_anki_deck(
                    "prompt",
                    "de",
                    "api-key",
                    "voice",
                    "edge",
                    None,
                )

            self.assertTrue(Path(apkg_path).exists())
            self.assertEqual(summary, "✅ das Wort")
            self.assertEqual(count, 1)
            self.assertEqual(len(media_files), 2)

        self.assertEqual(audio_mock.await_count, 2)
        anki_deck.add_note.assert_called_once()
        package.write_to_file.assert_called_once()


if __name__ == "__main__":
    unittest.main()
