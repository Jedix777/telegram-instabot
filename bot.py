import os
import logging
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # пример: https://mybot.onrender.com

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на Instagram-видео, и я попробую его скачать.")

# Основная логика обработки сообщений
async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    text = message.text or ""
    bot_username = context.bot.username

    # Проверяем, есть ли ссылка Instagram или упоминание бота
    has_instagram_link = "instagram.com" in text
    mentioned_bot = f"@{bot_username.lower()}" in text.lower()

    if not (has_instagram_link or mentioned_bot):
        return  # Игнорируем всё остальное

    # Ищем ссылку в тексте
    match = re.search(r"https?://(?:www\.)?instagram\.com/\S+", text)
    if not match:
        await message.reply_text("Пожалуйста, пришли корректную ссылку на Instagram.")
        return

    url = match.group(0)
    # await message.reply_text("Скачиваю видео, подожди немного...")

    try:
        ydl_opts = {
            "format": "best",
            "outtmpl": "video.%(ext)s",
            "quiet": True,
            "cookiefile": "cookies.txt",
            # "username": "antkopatich",
            # "password": "EDFRTGyh!345",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as f:
            await message.reply_video(video=f)

        os.remove(filename)

    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        await message.reply_text("Не удалось скачать видео 😢 Убедитесь, что ссылка рабочая, а куки актуальны.")

# Главная точка входа
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_link))

    # Запуск через Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()
