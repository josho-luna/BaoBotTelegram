import os
import time
import asyncio
import genanki
from google import genai
from audio import generate_audio
from structure import ankigen, FlashcardList, DECK_ID, TEMP_DIR

def generate_anki_deck(contents, user_lang, user_key, user_voice, tts_provider, el_key, deck_name = "BaoDrop"):
    gemini_client = genai.Client(api_key=user_key)
    
    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=contents,
        config={'response_mime_type': 'application/json', 'response_schema': FlashcardList}
    )
    
    flashcards = response.parsed.cards
    my_deck = genanki.Deck(DECK_ID, deck_name)
    all_media_files = []
    safe_id = str(int(time.time()))
    
    for index, card in enumerate(flashcards):
        word_audio_file = f"word_{safe_id}_{index}.mp3"
        sent_audio_file = f"sent_{safe_id}_{index}.mp3"
        
        word_audio_path = os.path.join(TEMP_DIR, word_audio_file)
        sent_audio_path = os.path.join(TEMP_DIR, sent_audio_file)
        
        asyncio.run(generate_audio(card.word, word_audio_path, user_voice, tts_provider, el_key))
        asyncio.run(generate_audio(card.example_sentence, sent_audio_path, user_voice, tts_provider, el_key))
        
        all_media_files.extend([word_audio_path, sent_audio_path])
        
        my_note = genanki.Note(
            model=ankigen(user_lang),
            fields=[
                card.word, card.pinyin, card.english, card.components,
                card.example_sentence, card.example_pinyin, card.example_translation,
                f"[sound:{word_audio_file}]", f"[sound:{sent_audio_file}]"
            ]
        )
        my_deck.add_note(my_note)
        
    apkg_filename = f"cards_{safe_id}.apkg"
    apkg_path = os.path.join(TEMP_DIR, apkg_filename)
    
    my_package = genanki.Package(my_deck)
    my_package.media_files = all_media_files
    my_package.write_to_file(apkg_path)
    
    summary_text = "\n".join([f"✅ {c.word} ({c.pinyin})" for c in flashcards])
    
    return apkg_path, summary_text, len(flashcards), all_media_files