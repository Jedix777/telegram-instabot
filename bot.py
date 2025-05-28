import os
import logging
import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота и ключ API
BOT_TOKEN = os.environ.get("BOT_TOKEN")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне ссылку на Instagram Reels или видео 📽️")

# Обработка ссылок Instagram
async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        await update.message.reply_text("Это не похоже на ссылку из Instagram.")
        return

    await update.message.reply_text("⏳ Скачиваю видео через API...")

    api_url = "https://instagram-downloader8.p.rapidapi.com/ig/download"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram-downloader8.p.rapidapi.com"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params={"url": url}, headers=headers)
            data = response.json()

        video_url = data.get("media")
        if not video_url:
            await update.message.reply_text("❌ Не удалось получить видео.")
            return

        async with httpx.AsyncClient() as client:
            video_response = await client.get(video_url)
            video_bytes = video_response.content

        await update.message.reply_video(video=video_bytes)

    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        await update.message.reply_text("🚫 Произошла ошибка при скачивании видео.")

# Запуск бота
async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_link))

    logging.info("Бот запущен. Ожидаю сообщения...")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
