import unittest
from string import Formatter
from unittest.mock import patch

from i18n import TRANSLATIONS, normalize_locale, translate


class LocaleTests(unittest.TestCase):
    def test_normalizes_regional_telegram_locale(self):
        self.assertEqual(normalize_locale("es-MX"), "es")
        self.assertEqual(normalize_locale("zh_CN"), "zh")

    def test_unsupported_locale_falls_back_to_english(self):
        self.assertEqual(normalize_locale("pt-BR"), "en")
        self.assertIn("Choose the language", translate("pt-BR", "choose_language"))

    def test_missing_translation_key_falls_back_to_english(self):
        with patch.dict(TRANSLATIONS["de"], {}, clear=True):
            self.assertEqual(translate("de", "provider_edge"), "Edge TTS (free)")

    def test_interpolates_localized_messages(self):
        message = translate("es", "language_updated", language="japonés")
        self.assertIn("japonés", message)

    def test_template_value_can_be_named_locale(self):
        message = translate(
            "en",
            "settings",
            language="German",
            deck_name="BaoDrop",
            provider="Edge TTS",
            gemini_status="configured",
            eleven_status="not configured",
            locale="English",
        )

        self.assertIn("Interface: English", message)

    def test_supported_locales_have_complete_catalogs_and_placeholders(self):
        english = TRANSLATIONS["en"]
        formatter = Formatter()
        for locale, messages in TRANSLATIONS.items():
            self.assertEqual(set(messages), set(english), locale)
            for key, template in messages.items():
                expected = {name for _, name, _, _ in formatter.parse(english[key]) if name}
                actual = {name for _, name, _, _ in formatter.parse(template) if name}
                self.assertEqual(actual, expected, f"{locale}.{key}")
                translate(locale, key, **{name: name for name in actual})


if __name__ == "__main__":
    unittest.main()
