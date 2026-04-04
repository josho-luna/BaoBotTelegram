import json
import os
from structure import PROFILES_FILE

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r") as f:
                content = f.read().strip()
                if not content: return {}
                data = json.loads(content)
                for chat_id, profile in data.items():
                    # Upgrade legacy string profiles to dicts
                    if isinstance(profile, str): 
                        data[chat_id] = {
                            "api_key": profile, 
                            "language": "🇨🇳 Chinese", 
                            "voice": "zh-CN-XiaoxiaoNeural",
                            "tts_provider": "edge",
                            "elevenlabs_key": None
                        }
                    elif isinstance(profile, dict):
                        if "tts_provider" not in profile:
                            profile["tts_provider"] = "edge"
                        if "elevenlabs_key" not in profile:
                            profile["elevenlabs_key"] = None
                        if "elevenlabs_voice" not in profile:
                            profile["elevenlabs_voice"] = "21m00Tcm4TlvDq8ikWAM"
                        if "deck_name" not in profile:
                            profile["deck_name"] = "BaoDrop"
                return data
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}

def save_profiles(data):
    with open(PROFILES_FILE, "w") as f:
        json.dump(data, f)