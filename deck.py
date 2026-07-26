import os
import uuid
import asyncio
import genanki
from google import genai
from audio import generate_audio
from structure import ankigen, FlashcardList, DECK_ID, TEMP_DIR


class EmptyDeckError(Exception):
    pass

def generate_anki_deck(contents, user_lang, user_key, user_voice, tts_provider, el_key, deck_name = "BaoDrop"):
    gemini_client = genai.Client(api_key=user_key)
    
    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=contents,
        config={'response_mime_type': 'application/json', 'response_schema': FlashcardList}
    )
    
    flashcards = response.parsed.cards
    if not flashcards:
        raise EmptyDeckError("The model returned no flashcards")
    my_deck = genanki.Deck(DECK_ID, deck_name)
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

            asyncio.run(generate_audio(card.word, word_audio_path, user_voice, tts_provider, el_key))
            asyncio.run(generate_audio(card.example_sentence, sent_audio_path, user_voice, tts_provider, el_key))

            my_note = genanki.Note(
                model=ankigen(user_lang),
                fields=[
                    card.word, card.pinyin, card.english, card.components,
                    card.example_sentence, card.example_pinyin, card.example_translation,
                    f"[sound:{word_audio_file}]", f"[sound:{sent_audio_file}]"
                ]
            )
            my_deck.add_note(my_note)

        my_package = genanki.Package(my_deck)
        my_package.media_files = all_media_files
        my_package.write_to_file(apkg_path)

        summary_cards = flashcards[:8]
        summary_text = "\n".join([f"✅ {c.word} ({c.pinyin})" for c in summary_cards])
        if len(flashcards) > len(summary_cards):
            summary_text += f"\n+{len(flashcards) - len(summary_cards)}"

        return apkg_path, summary_text, len(flashcards), all_media_files
    except Exception:
        for path in all_media_files + [apkg_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        raise
