import asyncio
import os
import uuid
from html import escape

import genanki
from google import genai

from audio import generate_audio
from config import DECK_ID, TARGET_LANGUAGES, TEMP_DIR
from structure import ankigen, FlashcardList


class EmptyDeckError(Exception):
    pass


def _anki_text(value):
    """Escape model-produced plain text before placing it in an HTML field."""
    return escape(value.strip(), quote=False)


def _note_fields(card, word_audio_file, sent_audio_file, language):
    language_config = TARGET_LANGUAGES[language]
    return [
        _anki_text(card.word),
        _anki_text(card.pronunciation),
        _anki_text(card.definition),
        _anki_text(card.notes),
        _anki_text(card.example_sentence),
        _anki_text(card.example_pronunciation),
        _anki_text(card.example_translation),
        f"[sound:{word_audio_file}]",
        f"[sound:{sent_audio_file}]",
        language,
        language_config["html_lang"],
        language_config["name"],
    ]


def _audio_text(card, language):
    """Prefer readings that remove script ambiguity without feeding IPA to TTS."""
    if language in {"ar", "ja"}:
        word = card.pronunciation.strip() or card.word
        sentence = card.example_pronunciation.strip() or card.example_sentence
        return word, sentence
    return card.word, card.example_sentence


def _is_usable_card(card, language):
    required_text = [
        card.word,
        card.definition,
        card.example_sentence,
        card.example_translation,
    ]
    if language in {"zh", "ar", "fr"}:
        required_text.append(card.pronunciation)
    if language in {"zh", "ar"}:
        required_text.append(card.example_pronunciation)
    return all(value.strip() for value in required_text)


def _format_summary(flashcards, limit=8):
    summary_cards = flashcards[:limit]
    lines = []
    for card in summary_cards:
        pronunciation = card.pronunciation.strip()
        pronunciation_hint = f" ({pronunciation})" if pronunciation else ""
        lines.append(f"✅ {card.word.strip()}{pronunciation_hint}")
    if len(flashcards) > len(summary_cards):
        lines.append(f"+{len(flashcards) - len(summary_cards)}")
    return "\n".join(lines)


def generate_anki_deck(
    contents,
    user_lang,
    user_key,
    user_voice,
    tts_provider,
    el_key,
    deck_name="BaoDrop",
):
    if user_lang not in TARGET_LANGUAGES:
        raise ValueError(f"Unsupported target language: {user_lang!r}")

    os.makedirs(TEMP_DIR, exist_ok=True)
    gemini_client = genai.Client(api_key=user_key)

    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=contents,
        config={"response_mime_type": "application/json", "response_schema": FlashcardList},
    )

    flashcards = [card for card in response.parsed.cards if _is_usable_card(card, user_lang)]
    if not flashcards:
        raise EmptyDeckError("The model returned no flashcards")
    my_deck = genanki.Deck(DECK_ID, deck_name)
    note_model = ankigen()
    all_media_files = []
    safe_id = uuid.uuid4().hex
    apkg_filename = f"cards_{safe_id}.apkg"
    apkg_path = os.path.join(TEMP_DIR, apkg_filename)

    try:
        for index, card in enumerate(flashcards):
            word_audio_file = f"word_{safe_id}_{index}.mp3"
            sent_audio_file = f"sent_{safe_id}_{index}.mp3"

            word_audio_path = os.path.join(TEMP_DIR, word_audio_file)
            sent_audio_path = os.path.join(TEMP_DIR, sent_audio_file)
            all_media_files.extend([word_audio_path, sent_audio_path])

            word_audio_text, sentence_audio_text = _audio_text(card, user_lang)
            asyncio.run(generate_audio(word_audio_text, word_audio_path, user_voice, tts_provider, el_key))
            asyncio.run(generate_audio(sentence_audio_text, sent_audio_path, user_voice, tts_provider, el_key))

            my_note = genanki.Note(
                model=note_model,
                fields=_note_fields(card, word_audio_file, sent_audio_file, user_lang),
            )
            my_deck.add_note(my_note)

        my_package = genanki.Package(my_deck)
        my_package.media_files = all_media_files
        my_package.write_to_file(apkg_path)

        summary_text = _format_summary(flashcards)

        return apkg_path, summary_text, len(flashcards), all_media_files
    except Exception:
        for path in all_media_files + [apkg_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        raise
