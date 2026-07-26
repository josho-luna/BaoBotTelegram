import json
import os
import tempfile
import threading
from i18n import normalize_locale
from config import PROFILES_FILE, SUPPORTED_LANGUAGES

DEFAULT_ELEVENLABS_VOICE = "21m00Tcm4TlvDq8ikWAM"
PROFILE_LOCK = threading.RLock()

LEGACY_LANGUAGES = {
    "🇨🇳 Chinese": "zh",
    "🇯🇵 Japanese": "ja",
    "🇰🇷 Korean": "ko",
    "🇲🇽 Spanish": "es",
    "🇪🇸 Spanish": "es",
    "🇵🇸 Arabic": "ar",
    "🇸🇦 Arabic": "ar",
    "🇫🇷 French": "fr",
    "🇩🇪 German": "de",
}


def create_profile(api_key=None, ui_locale="en"):
    profile = {
        "target_language": "zh",
        "ui_locale": normalize_locale(ui_locale),
        "tts_provider": "edge",
        "elevenlabs_key": None,
        "elevenlabs_voice": DEFAULT_ELEVENLABS_VOICE,
        "deck_name": "BaoDrop",
    }
    if api_key:
        profile["api_key"] = api_key
    return profile


def migrate_profile(profile):
    if isinstance(profile, str):
        return create_profile(api_key=profile)
    if not isinstance(profile, dict):
        return create_profile()

    migrated = create_profile(
        api_key=profile.get("api_key"),
        ui_locale=profile.get("ui_locale", "en"),
    )
    migrated.update(profile)
    legacy_language = profile.get("language")
    target_language = profile.get("target_language") or LEGACY_LANGUAGES.get(legacy_language, legacy_language)
    if target_language not in SUPPORTED_LANGUAGES:
        target_language = "zh"
    migrated["target_language"] = target_language
    migrated["ui_locale"] = normalize_locale(migrated.get("ui_locale"))
    migrated["tts_provider"] = (
        migrated.get("tts_provider") if migrated.get("tts_provider") in {"edge", "elevenlabs"} else "edge"
    )
    migrated["deck_name"] = migrated.get("deck_name") or "BaoDrop"
    migrated["elevenlabs_voice"] = migrated.get("elevenlabs_voice") or DEFAULT_ELEVENLABS_VOICE
    migrated.pop("language", None)
    migrated.pop("voice", None)
    return migrated

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r") as f:
                content = f.read().strip()
                if not content: return {}
                data = json.loads(content)
                for chat_id, profile in data.items():
                    data[chat_id] = migrate_profile(profile)
                return data
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}

def save_profiles(data):
    directory = os.path.dirname(os.path.abspath(PROFILES_FILE))
    temporary_path = None
    with PROFILE_LOCK:
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=directory, delete=False
            ) as profile_file:
                temporary_path = profile_file.name
                json.dump(data, profile_file, ensure_ascii=False)
                profile_file.flush()
                os.fsync(profile_file.fileno())
            os.replace(temporary_path, PROFILES_FILE)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.remove(temporary_path)
