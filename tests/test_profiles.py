import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

from profiles import create_profile, load_profiles, migrate_profile, save_profiles


class ProfileTests(unittest.TestCase):
    def test_new_profile_has_complete_defaults(self):
        profile = create_profile(ui_locale="fr-CA")

        self.assertEqual(profile["target_language"], "zh")
        self.assertEqual(profile["ui_locale"], "fr")
        self.assertEqual(profile["deck_name"], "BaoDrop")
        self.assertEqual(profile["tts_provider"], "edge")
        self.assertIn("elevenlabs_voice", profile)

    def test_migrates_legacy_display_language_to_stable_id(self):
        profile = migrate_profile({"api_key": "secret", "language": "🇲🇽 Spanish"})

        self.assertEqual(profile["target_language"], "es")
        self.assertNotIn("language", profile)
        self.assertNotIn("voice", profile)

    def test_repairs_partial_profile_values(self):
        profile = migrate_profile({"deck_name": None, "tts_provider": "unknown"})

        self.assertEqual(profile["deck_name"], "BaoDrop")
        self.assertEqual(profile["tts_provider"], "edge")

    def test_loads_and_migrates_legacy_string_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "profiles.json")
            with open(path, "w", encoding="utf-8") as profile_file:
                json.dump({"42": "secret"}, profile_file)

            with patch("profiles.PROFILES_FILE", path):
                profiles = load_profiles()

        self.assertEqual(profiles["42"]["api_key"], "secret")
        self.assertEqual(profiles["42"]["target_language"], "zh")

    def test_concurrent_saves_leave_valid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "profiles.json")
            with patch("profiles.PROFILES_FILE", path):
                threads = [
                    threading.Thread(target=save_profiles, args=({str(index): create_profile()},))
                    for index in range(8)
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                with open(path, encoding="utf-8") as profile_file:
                    saved = json.load(profile_file)

        self.assertEqual(len(saved), 1)


if __name__ == "__main__":
    unittest.main()
