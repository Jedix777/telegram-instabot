import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import yt_dlp

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне ссылку на Instagram Reels или видео.")

async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        await update.message.reply_text("Это не ссылка на Instagram.")
        return

    await update.message.reply_text("Скачиваю видео, подожди...")

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True,
            'cookiesfrombrowser': ('chrome',),  # если используешь cookies из браузера
            'cookiefile': 'cookies.txt'         # путь к cookies.txt
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as f:
            await update.message.reply_video(video=f)

        os.remove(filename)

    except Exception as e:
        logging.error(f"Ошибка при скачивании: {e}")
        await update.message.reply_text("Не удалось скачать видео 😢")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_link))

    logging.info("Бот запущен. Ожидаю сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()

