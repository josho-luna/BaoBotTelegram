import json
from textwrap import dedent

import genanki
from pydantic import BaseModel, Field

from config import MODEL_ID, TARGET_LANGUAGES


CSS = """
/* BaoCards multilingual v2. All fonts are offline-safe system stacks. */

.card {
  --background: #f5f7fa;
  --surface: #ffffff;
  --surface-muted: #eef2f6;
  --text: #17202a;
  --muted: #5f6b78;
  --accent: #087ea4;
  --note: #9a5a00;
  --divider: #d8dee6;
  --target-font: "Noto Sans", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --pronunciation-font: "Noto Sans", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --target-size: clamp(2.5rem, 12vw, 4.5rem);
  --target-spacing: normal;

  box-sizing: border-box;
  margin: 0;
  padding: 1rem;
  background: var(--background);
  color: var(--text);
  font-family: "Noto Sans", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 20px;
  line-height: 1.45;
  text-align: center;
}

.card.nightMode,
.card.night_mode,
.nightMode .card,
.night_mode .card {
  --background: #171a1f;
  --surface: #22272e;
  --surface-muted: #292f37;
  --text: #f4f6f8;
  --muted: #aeb8c3;
  --accent: #67c7f0;
  --note: #ffb866;
  --divider: #3b434d;
}

.card-shell {
  box-sizing: border-box;
  width: 100%;
  max-width: 42rem;
  margin: 0 auto;
}

.question-card {
  display: flex;
  min-height: 55vh;
  flex-direction: column;
  justify-content: center;
}

.language-zh {
  --target-font: "Kaiti SC", STKaiti, KaiTi, "楷体", "Noto Serif CJK SC", "Source Han Serif SC", serif;
  --target-size: clamp(3.2rem, 16vw, 5.4rem);
  --target-spacing: 0.035em;
}

.language-ja {
  --target-font: "Noto Sans CJK JP", "Yu Gothic", "Hiragino Sans", Meiryo, sans-serif;
  --pronunciation-font: "Noto Sans CJK JP", "Yu Gothic", "Hiragino Sans", Meiryo, sans-serif;
  --target-size: clamp(3rem, 15vw, 5rem);
}

.language-ko {
  --target-font: "Noto Sans CJK KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
  --pronunciation-font: "Noto Sans CJK KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
  --target-size: clamp(3rem, 15vw, 5rem);
}

.language-ar {
  --target-font: "Noto Naskh Arabic", "Geeza Pro", "Traditional Arabic", serif;
  --pronunciation-font: "Noto Naskh Arabic", "Geeza Pro", "Traditional Arabic", serif;
  --target-size: clamp(3rem, 15vw, 5.2rem);
  --target-spacing: normal;
}

.language-es {
  --target-font: "Noto Sans", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.language-fr {
  --target-font: "Noto Sans", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.language-de {
  --target-font: "Noto Sans", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.target-text {
  font-family: var(--target-font);
  font-kerning: normal;
  letter-spacing: var(--target-spacing);
  overflow-wrap: anywhere;
  text-rendering: optimizeLegibility;
  unicode-bidi: plaintext;
}

.language-ar .target-text {
  direction: rtl;
  letter-spacing: normal;
}

.language-ar .example-box {
  border-inline-start: 0;
  border-inline-end: 4px solid var(--accent);
}

.target-word {
  margin: 0.15em auto;
  color: var(--text);
  font-size: var(--target-size);
  font-weight: 500;
  line-height: 1.15;
}

.definition {
  margin: 0.45em 0;
  color: var(--text);
  font-size: 1.15em;
  font-weight: 650;
}

.language-label {
  display: inline-block;
  margin-bottom: 0.8em;
  padding: 0.2em 0.65em;
  border: 1px solid var(--divider);
  border-radius: 999px;
  color: var(--muted);
  font-size: 0.68em;
  font-weight: 650;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.pronunciation {
  margin: 0.3em 0 0.55em;
  color: var(--muted);
  font-family: var(--pronunciation-font);
  font-size: 0.9em;
  line-height: 1.4;
  unicode-bidi: plaintext;
}

.notes {
  margin: 0.7em auto;
  padding: 0.55em 0.75em;
  border-radius: 0.45em;
  background: var(--surface-muted);
  color: var(--note);
  font-size: 0.9em;
  text-align: start;
}

.audio {
  min-height: 1.2em;
  margin: 0.35em 0;
}

.example-box {
  margin-top: 1em;
  padding: 0.8em 1em;
  border-inline-start: 4px solid var(--accent);
  border-radius: 0.45em;
  background: var(--surface);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
  text-align: start;
}

.example-target {
  margin-bottom: 0.25em;
  color: var(--text);
  font-size: 1.6em;
  line-height: 1.35;
}

.example-pronunciation {
  margin-top: 0.3em;
  color: var(--muted);
  font-family: var(--pronunciation-font);
  font-size: 0.78em;
}

.example-translation {
  margin-top: 0.5em;
  color: var(--text);
  font-size: 0.95em;
}

hr {
  height: 1px;
  margin: 0.9em 0;
  border: 0;
  background: var(--divider);
}

@media (max-width: 420px) {
  .card {
    padding: 0.65rem;
    font-size: 18px;
  }

  .example-box {
    padding: 0.65em 0.75em;
  }
}
"""


TARGET_FRONT = """
{{#Word}}
<div class="card-shell question-card language-{{Language}}" lang="{{Locale}}">
  <div class="target-word target-text" lang="{{Locale}}" dir="auto">{{Word}}</div>
</div>
{{/Word}}
"""

DEFINITION_FRONT = """
{{#Definition}}
<div class="card-shell question-card language-{{Language}}" lang="{{Locale}}">
  <div class="language-label" lang="en" dir="ltr">{{LanguageName}}</div>
  <div class="definition" lang="en" dir="ltr">{{Definition}}</div>
</div>
{{/Definition}}
"""

ANSWER = """
<div class="card-shell language-{{Language}}" lang="{{Locale}}">
  <div class="target-word target-text" lang="{{Locale}}" dir="auto">{{Word}}</div>
  {{#Pronunciation}}
  <div class="pronunciation" lang="{{Locale}}" dir="auto">{{Pronunciation}}</div>
  {{/Pronunciation}}
  <div class="audio">{{WordAudio}}</div>

  <hr>
  <div class="definition" lang="en" dir="ltr">{{Definition}}</div>
  {{#Notes}}
  <div class="notes" lang="en" dir="ltr">{{Notes}}</div>
  {{/Notes}}

  <div class="example-box">
    <div class="example-target target-text" lang="{{Locale}}" dir="auto">{{Sentence}}</div>
    <div class="audio">{{SentenceAudio}}</div>
    {{#SentencePronunciation}}
    <div class="example-pronunciation" lang="{{Locale}}" dir="auto">{{SentencePronunciation}}</div>
    {{/SentencePronunciation}}
    <div class="example-translation" lang="en" dir="ltr">{{SentenceTranslation}}</div>
  </div>
</div>
"""


def ankigen():
    """Return the shared multilingual v2 Anki note type."""
    return genanki.Model(
        MODEL_ID,
        "BaoCards Multilingual v2",
        fields=[
            {"name": "Word"},
            {"name": "Pronunciation"},
            {"name": "Definition"},
            {"name": "Notes"},
            {"name": "Sentence"},
            {"name": "SentencePronunciation"},
            {"name": "SentenceTranslation"},
            {"name": "WordAudio"},
            {"name": "SentenceAudio"},
            {"name": "Language"},
            {"name": "Locale"},
            {"name": "LanguageName"},
        ],
        templates=[
            {
                "name": "Card 1 (Target -> Meaning)",
                "qfmt": TARGET_FRONT,
                "afmt": ANSWER,
            },
            {
                "name": "Card 2 (Meaning -> Target)",
                "qfmt": DEFINITION_FRONT,
                "afmt": ANSWER,
            },
        ],
        css=CSS,
    )


class FlashcardFields(BaseModel):
    word: str = Field(description="The target-language headword or useful fixed phrase")
    pronunciation: str = Field(description="The language-appropriate pronunciation aid, or an empty string")
    definition: str = Field(description="A concise English definition for the intended sense")
    notes: str = Field(description="Concise learning notes in English, or an empty string")
    example_sentence: str = Field(description="A short, natural target-language example")
    example_pronunciation: str = Field(
        description="The language-appropriate pronunciation aid for the example, or an empty string"
    )
    example_translation: str = Field(description="A natural English translation of the example")


class FlashcardList(BaseModel):
    cards: list[FlashcardFields]


LANGUAGE_GUIDANCE = {
    "zh": dedent(
        """
        - Use Simplified Chinese and standard Mainland Mandarin so spelling, Pinyin, fonts, and deck audio stay aligned.
        - `word`: use normal Chinese orthography; do not include Pinyin or a definition in this field.
        - `pronunciation` and `example_pronunciation`: always provide Hanyu Pinyin with tone marks, never tone numbers. Use natural word spacing and retain sentence punctuation.
        - `notes`: when useful, explain word composition, reliable character components, classifiers, or usage. Distinguish semantic and phonetic components and never invent an etymology.
        """
    ).strip(),
    "ja": dedent(
        """
        - Use standard contemporary Japanese orthography. Put verbs and adjectives in dictionary form unless the requested item is an inflected phrase.
        - `pronunciation`: give a kana reading when kanji or numerals make it useful. Use hiragana or katakana as natural; never use Romaji. Return an empty string when `word` is already transparent kana.
        - `example_pronunciation`: give the sentence's kana reading only when it contains kanji or numerals; otherwise return an empty string.
        - `notes`: include only useful kanji or morpheme composition, part of speech, transitivity, register, or usage. Do not guess pitch accent.
        """
    ).strip(),
    "ko": dedent(
        """
        - Use standard contemporary South Korean orthography. Put verbs and adjectives in their -다 dictionary form unless a fixed phrase requires otherwise.
        - `pronunciation` and `example_pronunciation`: use phonetic Hangul only when standard surface pronunciation differs materially from the spelling because of a sound change. Otherwise return an empty string. Never romanize Korean.
        - `notes`: include only useful morphology, speech level, honorific usage, particles, or a relevant sound-change explanation. Do not mechanically split Hangul syllable blocks.
        """
    ).strip(),
    "es": dedent(
        """
        - Use standard Spain Spanish so vocabulary, pronunciation, and deck audio stay aligned. Mention a strongly regional alternative in `notes` only when essential.
        - Include the usual singular article with common nouns in `word` when it teaches gender (for example, "la mano"); omit it where an article would be unnatural.
        - `pronunciation` and `example_pronunciation`: use broad IPA only for a loanword, unusual stress, dialect-sensitive form, or other genuinely non-obvious pronunciation. Otherwise return an empty string.
        - `notes`: include useful plural behavior, verb infinitive or irregular form, construction, register, or regional usage. Do not pad transparent words with a letter-by-letter breakdown.
        """
    ).strip(),
    "ar": dedent(
        """
        - Use Modern Standard Arabic so vocabulary, vocalization, fonts, and deck audio stay aligned. Keep `word` in normal, usually unvowelled Arabic orthography.
        - `pronunciation`: always give only the fully vowelled Arabic form with tashkil, without transliteration or labels. This field also supplies unambiguous word audio.
        - `example_pronunciation`: always give only the fully vowelled Arabic sentence, without transliteration or labels. This field also supplies unambiguous sentence audio.
        - `notes`: include a confidently known root/pattern, gender, broken or sound plural, governing preposition, or register when useful. Never force or invent a root analysis.
        """
    ).strip(),
    "fr": dedent(
        """
        - Use standard France French so vocabulary, pronunciation, and deck audio stay aligned. Mention a strongly regional alternative in `notes` only when essential.
        - Include the usual singular article with common nouns in `word` when it teaches gender (for example, "la maison"). If an elided article hides gender, state the gender in `notes`.
        - `pronunciation`: provide broad IPA for the headword or phrase.
        - `example_pronunciation`: provide broad IPA only when liaison, enchaînement, elision, or another spelling-sound mismatch makes it useful; otherwise return an empty string.
        - `notes`: include useful plural behavior, verb construction or irregular form, register, or usage. Keep separate senses on separate cards.
        """
    ).strip(),
    "de": dedent(
        """
        - Use contemporary Standard German. Capitalize nouns and use infinitives for verbs unless a fixed phrase requires otherwise.
        - Include the nominative definite article with common nouns in `word` (for example, "das Wort") so the reverse card tests gender as part of the item.
        - `pronunciation` and `example_pronunciation`: use broad IPA with primary stress only for borrowed, irregular, compound-stress, or otherwise ambiguous pronunciation. Otherwise return an empty string.
        - `notes`: include useful plural forms, verb principal parts/auxiliary/separable prefix, case government, register, or transparent compound morphology when relevant.
        """
    ).strip(),
}

if set(LANGUAGE_GUIDANCE) != set(TARGET_LANGUAGES):
    raise RuntimeError("Every configured target language needs prompt guidance")


def get_prompt(target_words, language):
    if language not in TARGET_LANGUAGES:
        raise ValueError(f"Unsupported target language: {language!r}")

    language_name = TARGET_LANGUAGES[language]["name"]
    learner_request = json.dumps(str(target_words).strip(), ensure_ascii=False)
    common_prompt = dedent(
        f"""
        You create accurate, study-ready {language_name} flashcards for English-speaking learners.

        The JSON string below is the learner's request. Use it to choose the topic, items, and requested count, but always follow this field contract and the {language_name} rules below.
        Learner request: {learner_request}

        Selection rules:
        - Follow an explicit requested count when practical.
        - Create one useful lexical item, collocation, or fixed phrase per card; do not make standalone cards for fragments that cannot stand alone.
        - Remove duplicates and near-duplicates. Prefer common, contemporary usage unless the learner asks otherwise.
        - Give each card one clear sense. Split unrelated meanings into separate cards.

        Field contract:
        - `word`: standard target-language orthography only. Do not add alternatives, pronunciation, labels, or an English gloss.
        - `pronunciation`: apply the language-specific policy below. If no aid is useful, return exactly an empty string, never "N/A", a dash, or a copy of `word`.
        - `definition`: a concise, context-specific English definition suitable as the prompt on a reverse card.
        - `notes`: only genuinely useful grammar, morphology, composition, register, or usage information, written concisely in English. Return an empty string rather than filler.
        - `example_sentence`: a short, natural, contemporary {language_name} sentence demonstrating the same sense; normal inflection is allowed.
        - `example_pronunciation`: apply the sentence-level policy below. Return exactly an empty string when it is unnecessary.
        - `example_translation`: a natural English translation matching the example sentence exactly.

        Quality rules:
        - Write the definitions, notes, and example translations in English. Keep target-language text out of English fields except where a quoted form is essential to a note.
        - Keep spelling, pronunciation, grammar, sense, example, and translation mutually consistent.
        - Do not invent roots, etymologies, pronunciation details, or grammatical facts. Omit uncertain optional information.
        - Return plain text in every field: no Markdown, HTML, labels, or explanatory preamble.
        - Return only data matching the supplied response schema.

        {language_name}-specific rules:
        """
    ).strip()
    return f"{common_prompt}\n{LANGUAGE_GUIDANCE[language]}"
