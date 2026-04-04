import io
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image

from profiles import load_profiles, save_profiles
from deck import generate_anki_deck
from structure import get_prompt, TELEGRAM_TOKEN, SUPPORTED_LANGUAGES, ELEVENLABS_VOICES

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_profiles = load_profiles()

def process_and_send(message, contents, status_text, user_lang, user_key, user_voice, tts_provider, el_key, user_deck_name):
    """Helper function to handle the UI state while the deck builds."""
    processing_msg = bot.reply_to(message, f"🥟 BaoBot is analyzing '{status_text}' to craft your {user_lang} deck...")
    
    try:
        apkg_path, summary_text, count, media_files = generate_anki_deck(
            contents, user_lang, user_key, user_voice, tts_provider, el_key, user_deck_name
        )
        
        caption = f"{summary_text}\n\nTap to import {count} {user_lang} card(s)!"
        
        with open(apkg_path, 'rb') as doc:
            bot.send_document(message.chat.id, doc, caption=caption)
            
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # Cleanup
        for f in media_files:
            if os.path.exists(f): os.remove(f)
        if os.path.exists(apkg_path): os.remove(apkg_path)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Oops, something broke: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🥟 Welcome to BaoBot!\n\n"
        "I can generate custom Anki flashcards with native audio for multiple languages.\n\n"
        "1. Get a free Google Gemini API Key in https://aistudio.google.com/app/apikey\n"
        "2. Send it to me using the command:\n"
        "\t\t/setkey YOUR_KEY_HERE\n"
        "3. Optionally you can add your ElevenLabs key for premium audio using:\n\t\t /elevenlabs YOUR_KEY\n or use \n\t/edgetts to use the free edge tts API\n"
        "4. Use /language to pick your target language or see the available ones!.\n"
        "\n\nText me a word, phrase, an Image or a prompt like 'list 5 colors'!"
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
    save_profiles(user_profiles)
    
    bot.answer_callback_query(call.id, f"Switched to {selected_lang}!")
    bot.edit_message_text(f"✅ Language updated to: **{selected_lang}**", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['setkey'])
def handle_setkey(message):
    chat_id = str(message.chat.id)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return bot.reply_to(message, "⚠️ Please include your key! Example: `/setkey AIzaSy...`", parse_mode="Markdown")
    
    if chat_id not in user_profiles: 
        user_profiles[chat_id] = {"language": "🇨🇳 Chinese", "tts_provider": "edge", "elevenlabs_key": None}
    
    user_profiles[chat_id]["api_key"] = parts[1].strip()
    save_profiles(user_profiles)
    
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    bot.send_message(message.chat.id, "✅ API Key saved securely! Send me text or a photo!")

@bot.message_handler(commands=['elevenlabs'])
def handle_elevenlabs_key(message):
    chat_id = str(message.chat.id)
    user = user_profiles[chat_id]


    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return bot.reply_to(message, "⚠️ Include your key! Example: `/elevenlabs sk_...`", parse_mode="Markdown")
    if chat_id not in user_profiles: return bot.reply_to(message, "🛑 Set your Gemini key first with /setkey!")
    
    user["elevenlabs_key"] = parts[1].strip()
    user["tts_provider"] = "elevenlabs"
    save_profiles(user_profiles)
    
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    bot.send_message(message.chat.id, "🎙️ ElevenLabs Key saved! Default Voice set to Alicia, use /elevenvoice VOICE_ID to set up a custom voice!")

@bot.message_handler(commands=['elevenvoice'])
def handle_elevenlabs_voice(message):
    chat_id = str(message.chat.id)
    user = user_profiles[chat_id]

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return bot.reply_to(message, "⚠️ Include your Voice ID! Example: `/elevenvoice 21m00...`", parse_mode="Markdown")
    if chat_id not in user_profiles: return bot.reply_to(message, "🛑 Set your Gemini key first with /setkey!")

    user["elevenlabs_voice"] = parts[1].strip()
    save_profiles(user_profiles)
    
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    bot.send_message(message.chat.id, "🎙️ ElevenLabs Voice ID saved!")


@bot.message_handler(commands=['deckname'])
def handle_elevenlabs_voice(message):
    chat_id = str(message.chat.id)
    user = user_profiles[chat_id]
    deckname = user["deck_name"]
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return bot.reply_to(message,f"Your current Deck Name is: *{deckname}* \nChange it with: `/deckname newDeckName`", parse_mode="Markdown")
    if chat_id not in user_profiles: return bot.reply_to(message, "🛑 Set your Gemini key first with /setkey!")

    user["deck_name"] = parts[1].strip()

    deckname = user["deck_name"]
    save_profiles(user_profiles)
    
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    bot.send_message(message.chat.id, f"🎙️ Custom Deck name updated to: '{deckname}'!")


@bot.message_handler(commands=['edgetts'])
def handle_edge_toggle(message):
    chat_id = str(message.chat.id)
    user = user_profiles[chat_id]
    if chat_id in user_profiles:
        user["tts_provider"] = "edge"
        save_profiles(user_profiles)
        bot.send_message(message.chat.id, "🗣️ Switched back to Edge TTS!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = str(message.chat.id)
    user = user_profiles[chat_id]

    if chat_id not in user_profiles or "api_key" not in user_profiles[chat_id]:
        return bot.reply_to(message, "🛑 Please send me a Gemini API key first!")

    

    user_lang = user.get('language', '🇨🇳 Chinese')
    user_key = user['api_key']
    tts_provider = user.get('tts_provider', 'edge')
    el_key = user.get('elevenlabs_key')
    user_voice = ELEVENLABS_VOICES.get(user_lang, "21m00Tcm4TlvDq8ikWAM") if (tts_provider == "elevenlabs" and el_key) else SUPPORTED_LANGUAGES.get(user_lang, "zh-CN-XiaoxiaoNeural")

    target_words = message.caption.strip() if message.caption else "Extract the most useful and common vocabulary words from this image."
    dynamic_prompt = get_prompt(target_words, user_lang)

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
    except Exception as e:
        return bot.reply_to(message, f"❌ Failed to download image from Telegram: {e}")

    contents = [image, dynamic_prompt]
    process_and_send(message, contents, "your image", user_lang, user_key, user_voice, tts_provider, el_key)

@bot.message_handler(content_types=['text'])
def handle_word(message):



    chat_id = str(message.chat.id)
    target_words = message.text.strip()
    user = user_profiles[chat_id]

    if chat_id not in user_profiles or "api_key" not in user:
        return bot.reply_to(message, "🛑 Please send me a Gemini API key first!")

    user_lang = user.get('language', '🇨🇳 Chinese')
    user_key = user['api_key']
    tts_provider = user.get('tts_provider', 'edge')
    el_key = user.get('elevenlabs_key')


    deck_name = user["deck_name"]
    if tts_provider == "elevenlabs" and el_key:
        user_voice = user.get("elevenlabs_voice") 
    elif tts_provider == "edge":
        user_voice = user.get("voice")
     

    dynamic_prompt = get_prompt(target_words, user_lang)
    process_and_send(message, dynamic_prompt, target_words, user_lang, user_key, user_voice, tts_provider, el_key, deck_name)

if __name__ == "__main__":
    print("🥟 BaoBot is online and ready to serve...")
    bot.infinity_polling()