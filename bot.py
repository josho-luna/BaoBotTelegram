import os
import time
import asyncio
import json
from dotenv import load_dotenv


import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
import edge_tts
import genanki

# Import models from structure.py
from structure import ankigen, FlashcardList, get_prompt

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


DECK_ID = 1938475620

TEMP_DIR = "anki_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
PROFILES_FILE = "user_profiles.json"

SUPPORTED_LANGUAGES = {
    "🇨🇳 Chinese": "zh-CN-XiaoxiaoNeural",
    "🇯🇵 Japanese": "ja-JP-NanamiNeural",
    "🇰🇷 Korean": "ko-KR-SunHiNeural",
    "🇲🇽 Spanish": "es-ES-ElviraNeural",
    "🇵🇸 Arabic": "ar-SA-ZariyahNeural",
    "🇫🇷 French": "fr-FR-DeniseNeural",
    "🇩🇪 German": "de-DE-KatjaNeural"
}


# User profiles {add ussage data sometime in the future}
def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r") as f:
                content = f.read().strip()
                if not content: return {}
                data = json.loads(content)
                
                # Auto-upgrade logic for old API keys
                for chat_id, profile in data.items():
                    if isinstance(profile, str): 
                        data[chat_id] = {
                            "api_key": profile, 
                            "language": "Chinese", 
                            "voice": "zh-CN-XiaoxiaoNeural"
                        }
                return data
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}

def save_profiles(data):
    with open(PROFILES_FILE, "w") as f:
        json.dump(data, f)

user_profiles = load_profiles()



# Audio gen with edge tts , todo: add elevenlabs support
async def generate_audio(text, filepath, voice):
    communicate = edge_tts.Communicate(text, voice, rate="-10%")
    await communicate.save(filepath)



# TELEGRAM HANDLERS
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🥟 Welcome to BaoBot!\n\n"
        "I can generate custom Anki flashcards with native audio for multiple languages.\n\n"
        "1. Get a free Google Gemini API Key (https://aistudio.google.com/app/apikey)\n"
        "2. Send it to me using the command:\n"
        "   /setkey YOUR_KEY_HERE\n"
        "3. Use /language to pick your target language.\n"
        "4. Text me a word, phrase, or a prompt like 'list 5 colors'!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['language'])
def choose_language(message):
    markup = InlineKeyboardMarkup()
    for lang in SUPPORTED_LANGUAGES.keys():
        markup.add(InlineKeyboardButton(lang, callback_data=f"lang_{lang}"))
    bot.reply_to(message, "🌍 What language are we learning today?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_language_selection(call):
    selected_lang = call.data.split('_')[1]
    chat_id = str(call.message.chat.id)
    
    if chat_id not in user_profiles:
        bot.answer_callback_query(call.id, "Send an API key first!", show_alert=True)
        return
        
    user_profiles[chat_id]['language'] = selected_lang
    user_profiles[chat_id]['voice'] = SUPPORTED_LANGUAGES[selected_lang]
    save_profiles(user_profiles)
    
    bot.answer_callback_query(call.id, f"Switched to {selected_lang}!")
    bot.edit_message_text(f"✅ Language updated to: **{selected_lang}**", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")

#  Set or update gemini API key
@bot.message_handler(commands=['setkey'])
def handle_setkey(message):
    chat_id = str(message.chat.id)
    # Split the message into the command and the key
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Please include your key! \n\nExample:\n`/setkey AIzaSy...`", parse_mode="Markdown")
        return
        
    new_key = parts[1].strip()
    
    # Initialize a fresh profile if they are new
    if chat_id not in user_profiles:
        user_profiles[chat_id] = {"language": "Chinese", "voice": "zh-CN-XiaoxiaoNeural"}
        
    user_profiles[chat_id]["api_key"] = new_key
    save_profiles(user_profiles)
    
    # Delete their message so the key isn't sitting in the chat history
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
        
    bot.send_message(message.chat.id, "✅ API Key saved securely! Use /language to pick your target, then send me a word!")



@bot.message_handler(func=lambda message: True)
def handle_word(message):
    chat_id = str(message.chat.id)
    target_words = message.text.strip()
    
    if chat_id not in user_profiles:
        bot.reply_to(message, "🛑 Please send me a Gemini API key first! (Starts with AIza...)")
        return

    user_lang = user_profiles[chat_id].get('language', 'Chinese')
    user_voice = user_profiles[chat_id].get('voice', 'zh-CN-XiaoxiaoNeural')
    user_key = user_profiles[chat_id]['api_key']

    processing_msg = bot.reply_to(message, f"🥟 BaoBot is crafting your {user_lang} deck for '{target_words}'...")
    
    try:
        gemini_client = genai.Client(api_key=user_key)
        dynamic_prompt = get_prompt(target_words, user_lang)
        
        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=dynamic_prompt,
            config={'response_mime_type': 'application/json', 'response_schema': FlashcardList}
        )
        
        flashcards = response.parsed.cards
        my_deck = genanki.Deck(DECK_ID, 'BaoDrop')
        all_media_files = []
        safe_id = str(int(time.time()))
        
        for index, card in enumerate(flashcards):
            word_audio_file = f"word_{safe_id}_{index}.mp3"
            sent_audio_file = f"sent_{safe_id}_{index}.mp3"
            
            word_audio_path = os.path.join(TEMP_DIR, word_audio_file)
            sent_audio_path = os.path.join(TEMP_DIR, sent_audio_file)
            
            asyncio.run(generate_audio(card.word, word_audio_path, user_voice))
            asyncio.run(generate_audio(card.example_sentence, sent_audio_path, user_voice))
            
            all_media_files.extend([word_audio_path, sent_audio_path])
            
            my_note = genanki.Note(
                model=ankigen(user_lang),
                fields=[
                    card.word,
                    card.pinyin,
                    card.english,
                    card.components,
                    card.example_sentence,
                    card.example_pinyin,
                    card.example_translation,
                    f"[sound:{word_audio_file}]",
                    f"[sound:{sent_audio_file}]"
                ]
            )
            my_deck.add_note(my_note)
            
        apkg_filename = f"cards_{safe_id}.apkg"
        apkg_path = os.path.join(TEMP_DIR, apkg_filename)
        
        my_package = genanki.Package(my_deck)
        my_package.media_files = all_media_files
        my_package.write_to_file(apkg_path)
        
        summary_text = "\n".join([f"✅ {c.word} ({c.pinyin})" for c in flashcards])
        caption = f"{summary_text}\n\nTap to import {len(flashcards)} {user_lang} card(s)!"
        
        with open(apkg_path, 'rb') as doc:
            bot.send_document(message.chat.id, doc, caption=caption)
            
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # Erase the evidence
        for media_file in all_media_files:
            if os.path.exists(media_file): os.remove(media_file)
        if os.path.exists(apkg_path): os.remove(apkg_path)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Oops, something broke: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)

if __name__ == "__main__":
    print("🥟 BaoBot is online and ready to serve...")
    bot.infinity_polling()