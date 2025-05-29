import os
import logging
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Например: https://mybot.onrender.com
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))  # Замените на свой Telegram user ID

COOKIES_FILE = "cookies.txt"

# Статистика для команды /status
stats = {
    "started_at": datetime.utcnow(),
    "total_downloads": 0,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь мне ссылку на Instagram или YouTube видео, и я попробую его скачать.\n"
        "Если хочешь, можешь отправить мне файл cookies в формате txt через команду /setcookies."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Извините, эта команда доступна только администратору.")
        return

    uptime = datetime.utcnow() - stats["started_at"]
    msg = (
        f"⏳ Время работы: {str(uptime).split('.')[0]}\n"
        f"🎥 Всего скачано видео: {stats['total_downloads']}"
    )
    await update.message.reply_text(msg)

async def set_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Извините, эта команда доступна только администратору.")
        return

    if not update.message.document:
        await update.message.reply_text("Пожалуйста, отправьте файл cookies.txt в формате txt.")
        return

    document = update.message.document
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("Пожалуйста, отправьте файл с расширением .txt.")
        return

    # Сохраняем файл cookies
    file = await document.get_file()
    await file.download_to_drive(COOKIES_FILE)

    await update.message.reply_text("Файл cookies успешно загружен и сохранён.")

async def handle_instagram_or_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not ("instagram.com" in url or "youtu" in url):
        await update.message.reply_text("Пожалуйста, отправьте ссылку с Instagram или YouTube.")
        return

    await update.message.reply_text("Скачиваю видео, подождите немного...")

    ydl_opts = {
        "format": "best",
        "outtmpl": "video.%(ext)s",
        "quiet": True,
    }

    # Если есть файл cookies - передаем в yt-dlp (для Instagram)
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as video_file:
            await update.message.reply_video(video=video_file)

        os.remove(filename)
        stats["total_downloads"] += 1

    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        await update.message.reply_text(
            "Не удалось скачать видео 😢 Возможно, ссылка недоступна или нужны актуальные cookies."
        )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("setcookies", set_cookies))

    # Фильтр: текстовые сообщения, которые содержат ссылки Instagram или YouTube, не команды
    link_filter = (
        filters.TEXT
        & ~filters.COMMAND
        & filters.Regex(r"https?://")
        & filters.Regex(r"(instagram\.com|youtu)")
    )
    app.add_handler(MessageHandler(link_filter, handle_instagram_or_youtube_link))

    # Запуск Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()

