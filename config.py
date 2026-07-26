import os

from dotenv import load_dotenv

load_dotenv()

MODEL_ID = 1847563921
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DECK_ID = 1938475620
TEMP_DIR = "anki_temp"
PROFILES_FILE = "user_profiles.json"

TARGET_LANGUAGES = {
    "zh": {"name": "Chinese", "flag": "🇨🇳", "edge_voice": "zh-CN-XiaoxiaoNeural"},
    "ja": {"name": "Japanese", "flag": "🇯🇵", "edge_voice": "ja-JP-NanamiNeural"},
    "ko": {"name": "Korean", "flag": "🇰🇷", "edge_voice": "ko-KR-SunHiNeural"},
    "es": {"name": "Spanish", "flag": "🇪🇸", "edge_voice": "es-ES-ElviraNeural"},
    "ar": {"name": "Arabic", "flag": "🇸🇦", "edge_voice": "ar-SA-ZariyahNeural"},
    "fr": {"name": "French", "flag": "🇫🇷", "edge_voice": "fr-FR-DeniseNeural"},
    "de": {"name": "German", "flag": "🇩🇪", "edge_voice": "de-DE-KatjaNeural"},
}

SUPPORTED_LANGUAGES = {
    language_id: config["edge_voice"] for language_id, config in TARGET_LANGUAGES.items()
}
ELEVENLABS_VOICES = {language_id: "21m00Tcm4TlvDq8ikWAM" for language_id in TARGET_LANGUAGES}
