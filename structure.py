import genanki
from pydantic import BaseModel

from dotenv import load_dotenv
import os

load_dotenv()

MODEL_ID = 1847563921

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DECK_ID = 1938475620
TEMP_DIR = "anki_temp"
PROFILES_FILE = "user_profiles.json"

os.makedirs(TEMP_DIR, exist_ok=True)

SUPPORTED_LANGUAGES = {
    "🇨🇳 Chinese": "zh-CN-XiaoxiaoNeural",
    "🇯🇵 Japanese": "ja-JP-NanamiNeural",
    "🇰🇷 Korean": "ko-KR-SunHiNeural",
    "🇲🇽 Spanish": "es-ES-ElviraNeural",
    "🇵🇸 Arabic": "ar-SA-ZariyahNeural",
    "🇫🇷 French": "fr-FR-DeniseNeural",
    "🇩🇪 German": "de-DE-KatjaNeural"
}

ELEVENLABS_VOICES = {
    "🇨🇳 Chinese": "21m00Tcm4TlvDq8ikWAM", 
    "🇯🇵 Japanese": "21m00Tcm4TlvDq8ikWAM",
    "🇰🇷 Korean": "21m00Tcm4TlvDq8ikWAM",
    "🇲🇽 Spanish": "21m00Tcm4TlvDq8ikWAM",
    "🇵🇸 Arabic": "21m00Tcm4TlvDq8ikWAM",
    "🇫🇷 French": "21m00Tcm4TlvDq8ikWAM",
    "🇩🇪 German": "21m00Tcm4TlvDq8ikWAM"
}

CSS = """
/* ---------- DARK-MODE SAFE ---------- */

@import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&display=swap');

@font-face {
  font-family: "Cool";
  src: url("_AdobeKaitiStdR.otf");
}

:root {
  --bg-dark: #1e1e1e;
  --text-dark: #FFF;
  --accent-dark: #4fbcff;
  --pinyin-dark: #a0a0a0;
  --divider-dark: #444;
  --radical-dark: #ff9f43;
  --font-hanzi: "Cool", "Ma Shan Zheng", cursive, arial;
  --font-main:arial;
  --font-mono: monospace;
}

.card {
  font-family: var(--font-main);
  font-size: 20px;
  text-align: center;
  background: var(--bg-dark);
  color: var(--text-dark);
  padding: 0.8em;
  line-height: 1.35;
}

.hanzi {
  font-family:var(--font-hanzi);
  font-size: 80px;
  line-height: 1.1;
  margin: 0 auto;
  letter-spacing: 0.05em;
  color: #FFF;
}

.pinyin {
  color: var(--pinyin-dark);
  font-family: var(--font-mono);
  font-size: 0.9em; 
  margin-bottom: 5px;
}

.blur-guard {
  filter: blur(6px);
  user-select: none;
  cursor: pointer;
  transition: filter 0.2s ease;
  background: rgba(255,255,255,0.05); 
  border-radius: 4px;
  padding: 2px 8px;
  display: inline-block; 
}

.blur-guard.reveal {
  filter: none;
  background: transparent;
}

.english {
  font-size: 1.1em;
  font-weight: 600;
  margin: 0.4em 0;
  color: var(--text-dark);
}

.components {
  font-size: 0.95em;
  color: var(--radical-dark);
  margin: 0.5em 0;
}

.example-box {
  margin-top: 1em;
  padding: 0.6em 1em;
  border-left: 4px solid var(--accent-dark);
  background: #2a2a2a;
  text-align: left;
  border-radius: 4px;
}

.example-hanzi {
  font-family:var(--font-hanzi);
  font-size: 1.7em;
  color: var(--text-dark);
  margin-bottom: 0.25em;
}

.example-pinyin {
  font-size: 0.7em;
  color: var(--pinyin-dark);
  font-family: var(--font-mono);
  margin-top: 5px;
}

.example-translation {
  font-size: 0.95em;
  color: var(--text-dark);
  margin-top: 0.3em;
}

hr {
  border: none;
  height: 1px;
  background: var(--divider-dark);
  margin: 0.8em 0;
}
"""

def ankigen(language): 
  return genanki.Model(
    MODEL_ID,
    f'BaoCards{language}',
    fields=[
        {'name': 'Word'},
        {'name': 'Pinyin'},
        {'name': 'English'},
        {'name': 'Components'},
        {'name': 'Sentence'},
        {'name': 'SentencePinyin'}, 
        {'name': 'SentenceTranslation'},
        {'name': 'WordAudio'},
        {'name': 'SentenceAudio'},
    ],
    templates=[
        {
            'name': 'Card 1 (Target -> English)',
            'qfmt': """
                <span class="hanzi">{{Word}}</span>
                
            """,
            'afmt': """
                <div class="hanzi">{{Word}}</div>
                <hr>
                <div class="pinyin blur-guard" onclick="this.classList.toggle('reveal')">{{Pinyin}}</div>
                <div class="english">{{English}}</div>
                <div class="components">{{Components}}</div>
                word: {{WordAudio}}
                sentence:  {{SentenceAudio}}
                <div class="example-box">
                    <div class="example-translation">{{SentenceTranslation}}</div>
                    <div class="example-hanzi">{{Sentence}}</div>
                    <div class="example-pinyin blur-guard" onclick="this.classList.toggle('reveal')">
                        {{SentencePinyin}}
                    </div>
                </div>
            """,
        },
        {
            'name': 'Card 2 (English -> Target)',
            'qfmt': """
                <div class="card">
                    <div class="english" style="font-size: 1.6em; margin-top: 40px;">{{English}}</div>
                    <hr style="width: 50%; margin: 20px auto; opacity: 0.5;">
                </div>
            """,
            'afmt': """
                <div class="card">
                    <div class="english" style="font-size: 1em; color: #888; margin-bottom: 10px;">{{English}}</div>
                    <span class="hanzi">{{Word}}</span> 
                    <div class="components">{{Components}}</div>
                    <div class="example-pinyin blur-guard"  onclick="this.classList.toggle('reveal')" style="color: var(--accent-dark); font-size: 1.2em; margin: 10px 0;">{{Pinyin}}</div>
                    <div style="margin: 15px 0; font-size: 0.8em;">
                        Word:  {{WordAudio}} &nbsp; Sent: {{SentenceAudio}}
                    </div>
                    <hr>
                    <div class="example-box">
                        <div class="example-translation">{{SentenceTranslation}}</div>
                        <div class="example-hanzi">{{Sentence}}</div>
                        <div class="example-pinyin blur-guard" onclick="this.classList.toggle('reveal')">
                            {{SentencePinyin}}
                        </div>
                    </div>
                </div>
            """,
        },
    ], 
    css=CSS
)

# STRUCTURED OUTPUT MODELS

class FlashcardFields(BaseModel):
    word: str
    pinyin: str
    english: str
    components: str
    example_sentence: str
    example_pinyin: str
    example_translation: str

class FlashcardList(BaseModel):
    cards: list[FlashcardFields]

def get_prompt(target_words, language):
    return f"""
    Create {language} flashcards for the following words/phrases/request: {target_words}. 
    - For 'components', provide a root breakdown or character breakdown. 
    - For 'pinyin', provide the standard pronunciation guide (e.g., Pinyin for Chinese, Romaji for Japanese).
    - For 'example_pinyin', do the same for the example sentence.
    Return a list of flashcards.
    """





