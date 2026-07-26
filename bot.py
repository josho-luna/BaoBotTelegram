import io
import logging
import os

import telebot
from PIL import Image
from telebot.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

from deck import EmptyDeckError, generate_anki_deck
from config import ELEVENLABS_VOICES, SUPPORTED_LANGUAGES, TARGET_LANGUAGES, TELEGRAM_TOKEN
from i18n import UI_LOCALES, normalize_locale, translate
from profiles import PROFILE_LOCK, create_profile, load_profiles, save_profiles
from structure import get_prompt

logger = logging.getLogger(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_profiles = load_profiles()


def get_chat_id(message):
    return str(message.chat.id)


def telegram_locale(source):
    user = getattr(source, "from_user", None)
    return normalize_locale(getattr(user, "language_code", None))


def get_or_create_profile(source):
    message = getattr(source, "message", source)
    chat_id = get_chat_id(message)
    with PROFILE_LOCK:
        if chat_id not in user_profiles:
            user_profiles[chat_id] = create_profile(ui_locale=telegram_locale(source))
        return user_profiles[chat_id]


def update_profile(source, **changes):
    with PROFILE_LOCK:
        profile = get_or_create_profile(source)
        profile.update(changes)
        save_profiles(user_profiles)
        return profile


def get_locale(source):
    message = getattr(source, "message", source)
    profile = user_profiles.get(get_chat_id(message))
    return profile.get("ui_locale", telegram_locale(source)) if profile else telegram_locale(source)


def text(source, key, **values):
    return translate(get_locale(source), key, **values)


def target_label(language_id, locale):
    config = TARGET_LANGUAGES[language_id]
    return f'{config["flag"]} {translate(locale, f"target_{language_id}")}'


def require_api_key(message):
    if not is_private_chat(message):
        bot.reply_to(message, text(message, "private_only"))
        return None
    profile = get_or_create_profile(message)
    if not profile.get("api_key"):
        bot.reply_to(message, text(message, "api_key_required"))
        return None
    return profile


def is_private_chat(message):
    return getattr(message.chat, "type", "private") == "private"


def delete_secret_message(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        logger.info("Could not delete a credential message from chat %s", message.chat.id)


def process_and_send(message, contents, status_text, profile):
    locale = get_locale(message)
    language_id = profile["target_language"]
    language = target_label(language_id, locale)
    preview = status_text.strip().replace("\n", " ")[:120]
    if len(status_text.strip()) > 120:
        preview += "..."

    processing_msg = bot.reply_to(
        message,
        translate(locale, "processing", language=language, preview=preview),
    )
    apkg_path = None
    media_files = []
    delivered = False

    try:
        tts_provider = profile.get("tts_provider", "edge")
        elevenlabs_key = profile.get("elevenlabs_key")
        if tts_provider == "elevenlabs" and elevenlabs_key:
            voice = profile.get("elevenlabs_voice") or ELEVENLABS_VOICES[language_id]
        else:
            tts_provider = "edge"
            voice = SUPPORTED_LANGUAGES[language_id]

        apkg_path, summary, count, media_files = generate_anki_deck(
            contents,
            language_id,
            profile["api_key"],
            voice,
            tts_provider,
            elevenlabs_key,
            profile.get("deck_name", "BaoDrop"),
        )
        caption_key = "deck_caption_one" if count == 1 else "deck_caption_many"
        caption = translate(locale, caption_key, count=count, language=language)
        if summary:
            caption = f"{summary}\n\n{caption}"
        caption = caption[:1024]

        with open(apkg_path, "rb") as document:
            bot.send_document(message.chat.id, document, caption=caption)
        delivered = True
    except EmptyDeckError:
        bot.edit_message_text(
            translate(locale, "empty_result"),
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
        )
    except Exception:
        logger.exception("Deck generation failed for chat %s", message.chat.id)
        bot.edit_message_text(
            translate(locale, "generation_failed"),
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
        )
    finally:
        for path in media_files + ([apkg_path] if apkg_path else []):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError:
                logger.warning("Could not remove temporary file %s", path, exc_info=True)

    if delivered:
        try:
            bot.delete_message(message.chat.id, processing_msg.message_id)
        except Exception:
            logger.info("Could not remove progress message in chat %s", message.chat.id)


@bot.message_handler(commands=["start", "help"])
def send_help(message):
    bot.reply_to(message, text(message, "help"), disable_web_page_preview=True)


@bot.message_handler(commands=["language"])
def choose_language(message):
    profile = get_or_create_profile(message)
    locale = get_locale(message)
    buttons = []
    for language_id in TARGET_LANGUAGES:
        label = target_label(language_id, locale)
        if language_id == profile["target_language"]:
            label = f"✓ {label}"
        buttons.append(InlineKeyboardButton(label, callback_data=f"target:{language_id}"))
    markup = InlineKeyboardMarkup([buttons[index:index + 2] for index in range(0, len(buttons), 2)])
    bot.reply_to(message, translate(locale, "choose_language"), reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("target:"))
def handle_language_selection(call):
    language_id = call.data.removeprefix("target:")
    locale = get_locale(call)
    if language_id not in TARGET_LANGUAGES:
        bot.answer_callback_query(call.id, translate(locale, "invalid_selection"), show_alert=True)
        return

    update_profile(call, target_language=language_id)
    language = target_label(language_id, locale)
    bot.answer_callback_query(call.id, translate(locale, "language_updated", language=language))
    bot.edit_message_text(
        translate(locale, "language_updated", language=language),
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_legacy_language_selection(call):
    bot.answer_callback_query(call.id, text(call, "invalid_selection"), show_alert=True)


@bot.message_handler(commands=["locale"])
def choose_locale(message):
    profile = get_or_create_profile(message)
    buttons = []
    for locale_id, locale_name in UI_LOCALES.items():
        label = f"✓ {locale_name}" if locale_id == profile["ui_locale"] else locale_name
        buttons.append(InlineKeyboardButton(label, callback_data=f"locale:{locale_id}"))
    markup = InlineKeyboardMarkup([buttons[index:index + 2] for index in range(0, len(buttons), 2)])
    bot.reply_to(message, text(message, "choose_locale"), reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("locale:"))
def handle_locale_selection(call):
    locale = call.data.removeprefix("locale:")
    if locale not in UI_LOCALES:
        bot.answer_callback_query(call.id, text(call, "invalid_selection"), show_alert=True)
        return

    update_profile(call, ui_locale=locale)
    confirmation = translate(locale, "locale_updated")
    bot.answer_callback_query(call.id, confirmation)
    bot.edit_message_text(
        confirmation,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )


@bot.message_handler(commands=["setkey"])
def handle_setkey(message):
    if not is_private_chat(message):
        bot.reply_to(message, text(message, "private_only"))
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, text(message, "key_usage"))
        return

    update_profile(message, api_key=parts[1].strip())
    delete_secret_message(message)
    bot.send_message(message.chat.id, text(message, "key_saved"))


@bot.message_handler(commands=["elevenlabs"])
def handle_elevenlabs_key(message):
    if not is_private_chat(message):
        bot.reply_to(message, text(message, "private_only"))
        return
    profile = require_api_key(message)
    if not profile:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, text(message, "eleven_key_usage"))
        return

    update_profile(
        message,
        elevenlabs_key=parts[1].strip(),
        tts_provider="elevenlabs",
    )
    delete_secret_message(message)
    bot.send_message(message.chat.id, text(message, "eleven_saved"))


@bot.message_handler(commands=["elevenvoice"])
def handle_elevenlabs_voice(message):
    profile = require_api_key(message)
    if not profile:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, text(message, "voice_usage"))
        return

    update_profile(message, elevenlabs_voice=parts[1].strip())
    bot.send_message(message.chat.id, text(message, "voice_saved"))


@bot.message_handler(commands=["deckname"])
def handle_deck_name(message):
    profile = get_or_create_profile(message)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, text(message, "deck_current", deck_name=profile["deck_name"]))
        return

    deck_name = parts[1].strip()[:100]
    update_profile(message, deck_name=deck_name)
    bot.send_message(message.chat.id, text(message, "deck_updated", deck_name=deck_name))


@bot.message_handler(commands=["edgetts"])
def handle_edge_toggle(message):
    update_profile(message, tts_provider="edge")
    bot.send_message(message.chat.id, text(message, "edge_enabled"))


@bot.message_handler(commands=["settings"])
def show_settings(message):
    profile = get_or_create_profile(message)
    locale = get_locale(message)
    configured = translate(locale, "configured")
    not_configured = translate(locale, "not_configured")
    provider = translate(locale, f'provider_{profile.get("tts_provider", "edge")}')
    bot.reply_to(
        message,
        translate(
            locale,
            "settings",
            language=target_label(profile["target_language"], locale),
            deck_name=profile["deck_name"],
            provider=provider,
            gemini_status=configured if profile.get("api_key") else not_configured,
            eleven_status=configured if profile.get("elevenlabs_key") else not_configured,
            locale=UI_LOCALES[locale],
        ),
    )


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    profile = require_api_key(message)
    if not profile:
        return

    target_words = (message.caption or "").strip()
    if not target_words:
        target_words = "Extract the most useful and common vocabulary words from this image."
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
        image.load()
    except Exception:
        logger.exception("Could not download photo for chat %s", message.chat.id)
        bot.reply_to(message, text(message, "image_failed"))
        return

    contents = [image, get_prompt(target_words, profile["target_language"])]
    try:
        process_and_send(message, contents, text(message, "image_preview"), profile)
    finally:
        image.close()


@bot.message_handler(func=lambda message: bool(message.text and message.text.startswith("/")), content_types=["text"])
def handle_unknown_command(message):
    bot.reply_to(message, text(message, "unknown_command"))


@bot.message_handler(func=lambda message: bool(message.text and not message.text.startswith("/")), content_types=["text"])
def handle_text(message):
    profile = require_api_key(message)
    if not profile:
        return
    target_words = message.text.strip()
    if not target_words:
        bot.reply_to(message, text(message, "empty_prompt"))
        return

    prompt = get_prompt(target_words, profile["target_language"])
    process_and_send(message, prompt, target_words, profile)


@bot.message_handler(content_types=["audio", "document", "sticker", "video", "video_note", "voice"])
def handle_unsupported_content(message):
    bot.reply_to(message, text(message, "unsupported_content"))


def register_commands():
    command_keys = [
        ("start", "command_start"),
        ("help", "command_help"),
        ("language", "command_language"),
        ("locale", "command_locale"),
        ("settings", "command_settings"),
        ("deckname", "command_deckname"),
        ("edgetts", "command_edgetts"),
    ]
    for locale in UI_LOCALES:
        commands = [BotCommand(command, translate(locale, key)) for command, key in command_keys]
        kwargs = {} if locale == "en" else {"language_code": locale}
        try:
            bot.set_my_commands(commands, **kwargs)
        except Exception:
            logger.warning("Could not register Telegram commands for locale %s", locale, exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    register_commands()
    logger.info("BaoBot is online and ready")
    bot.infinity_polling()
