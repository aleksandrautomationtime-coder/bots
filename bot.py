# -*- coding: utf-8 -*-
"""
Бот: /yt — транскрипт YouTube, /tg — посты Telegram-канала.
Вся логика в этой папке, можно загружать только её на GitHub.
"""
import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from transcript import get_transcript, extract_video_id
from parse_channel import fetch_posts, normalize_username
from config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4096

STATE_YT_LINK = "await_yt_link"
STATE_TG_LINK = "await_tg_link"
STATE_TG_COUNT = "await_tg_count"
KEY_TG_CHANNEL = "tg_channel"


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "Команды:\n\n"
        "/yt — транскрипт YouTube (по запросу пришлю ссылку).\n\n"
        "/tg — посты канала: ссылка на канал → количество постов.\n\n"
        "/cancel — отменить ввод."
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for k in (STATE_YT_LINK, STATE_TG_LINK, STATE_TG_COUNT, KEY_TG_CHANNEL):
        context.user_data.pop(k, None)
    await update.message.reply_text("Ввод отменён.")


async def cmd_yt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[STATE_YT_LINK] = True
    context.user_data.pop(STATE_TG_LINK, None)
    context.user_data.pop(STATE_TG_COUNT, None)
    context.user_data.pop(KEY_TG_CHANNEL, None)
    await update.message.reply_text("Отправьте ссылку на YouTube (или youtu.be).")


async def handle_yt_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not extract_video_id(text):
        await update.message.reply_text("Не похоже на ссылку YouTube. Отправьте ссылку или /cancel.")
        return
    context.user_data.pop(STATE_YT_LINK, None)
    await update.message.reply_text("Получаю транскрипт…")
    try:
        transcript = get_transcript(text, languages=["ru", "en"])
    except Exception as e:
        logger.exception("yt error")
        await update.message.reply_text(f"Ошибка: {e}")
        return
    if not transcript:
        await update.message.reply_text("Не удалось получить транскрипт.")
        return
    if len(transcript) <= MAX_MESSAGE_LENGTH:
        await update.message.reply_text(transcript)
    else:
        for i in range(0, len(transcript), MAX_MESSAGE_LENGTH):
            await update.message.reply_text(transcript[i : i + MAX_MESSAGE_LENGTH])
            await asyncio.sleep(0.3)
    await update.message.reply_text("Готово.")


async def cmd_tg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[STATE_TG_LINK] = True
    context.user_data.pop(STATE_YT_LINK, None)
    context.user_data.pop(STATE_TG_COUNT, None)
    context.user_data.pop(KEY_TG_CHANNEL, None)
    await update.message.reply_text("Отправьте ссылку на канал (t.me/s/username или t.me/username).")


async def handle_tg_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    channel = normalize_username(text)
    if not channel:
        await update.message.reply_text("Не удалось извлечь канал. Отправьте ссылку или /cancel.")
        return
    context.user_data.pop(STATE_TG_LINK, None)
    context.user_data[KEY_TG_CHANNEL] = channel
    context.user_data[STATE_TG_COUNT] = True
    await update.message.reply_text("Сколько последних постов вывести? (число)")


async def handle_tg_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    try:
        limit = max(1, min(100, int(text)))
    except ValueError:
        await update.message.reply_text("Введите число (например 10) или /cancel.")
        return
    channel = context.user_data.get(KEY_TG_CHANNEL)
    context.user_data.pop(STATE_TG_COUNT, None)
    context.user_data.pop(KEY_TG_CHANNEL, None)
    if not channel:
        await update.message.reply_text("Сессия сброшена. Начните заново: /tg")
        return
    await update.message.reply_text(f"Парсю @{channel}…")
    try:
        posts = fetch_posts(channel, limit=limit)
    except Exception as e:
        logger.exception("tg error")
        await update.message.reply_text(f"Ошибка: {e}")
        return
    if not posts:
        await update.message.reply_text("Постов не найдено или канал недоступен.")
        return
    for i, p in enumerate(posts, 1):
        date = (p.get("date") or "")[:10]
        txt = (p.get("text") or "").strip() or "(медиа)"
        msg = f"#{i} {date}\n{txt[:800]}{'…' if len(txt) > 800 else ''}"
        if len(msg) > MAX_MESSAGE_LENGTH:
            msg = msg[: MAX_MESSAGE_LENGTH - 20] + "…"
        await update.message.reply_text(msg)
        await asyncio.sleep(0.25)
    await update.message.reply_text(f"Готово. Постов: {len(posts)}.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    if context.user_data.get(STATE_YT_LINK):
        await handle_yt_link(update, context)
        return
    if context.user_data.get(STATE_TG_LINK):
        await handle_tg_link(update, context)
        return
    if context.user_data.get(STATE_TG_COUNT):
        await handle_tg_count(update, context)
        return
    await update.message.reply_text("Используйте /yt или /tg. /start — справка.")


def main() -> None:
    if not BOT_TOKEN:
        print("Задайте BOT_TOKEN в .env в этой папке.")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("yt", cmd_yt))
    app.add_handler(CommandHandler("tg", cmd_tg))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
