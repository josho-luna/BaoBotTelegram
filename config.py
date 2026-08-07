import os

from dotenv import load_dotenv

load_dotenv()

# The multilingual v2 note type intentionally has a new ID.  Reusing the old
# Chinese-shaped schema would make Anki merge incompatible fields on import.
MODEL_ID = 1847563922
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DECK_ID = 1938475620
TEMP_DIR = "anki_temp"
PROFILES_FILE = "user_profiles.json"

TARGET_LANGUAGES = {
    "zh": {
        "name": "Chinese",
        "flag": "🇨🇳",
        "html_lang": "zh-Hans",
        "edge_voice": "zh-CN-XiaoxiaoNeural",
    },
    "ja": {
        "name": "Japanese",
        "flag": "🇯🇵",
        "html_lang": "ja-JP",
        "edge_voice": "ja-JP-NanamiNeural",
    },
    "ko": {
        "name": "Korean",
        "flag": "🇰🇷",
        "html_lang": "ko-KR",
        "edge_voice": "ko-KR-SunHiNeural",
    },
    "es": {
        "name": "Spanish",
        "flag": "🇪🇸",
        "html_lang": "es-ES",
        "edge_voice": "es-ES-ElviraNeural",
    },
    "ar": {
        "name": "Arabic",
        "flag": "🇸🇦",
        "html_lang": "ar",
        "edge_voice": "ar-SA-ZariyahNeural",
    },
    "fr": {
        "name": "French",
        "flag": "🇫🇷",
        "html_lang": "fr-FR",
        "edge_voice": "fr-FR-DeniseNeural",
    },
    "de": {
        "name": "German",
        "flag": "🇩🇪",
        "html_lang": "de-DE",
        "edge_voice": "de-DE-KatjaNeural",
    },
}

SUPPORTED_LANGUAGES = {
    language_id: config["edge_voice"] for language_id, config in TARGET_LANGUAGES.items()
}
ELEVENLABS_VOICES = {language_id: "21m00Tcm4TlvDq8ikWAM" for language_id in TARGET_LANGUAGES}
