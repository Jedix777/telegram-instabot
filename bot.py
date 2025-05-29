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
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))  # Ваш Telegram ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь мне ссылку на видео с Instagram или YouTube, и я попробую его скачать."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return
    await update.message.reply_text("Бот работает нормально. " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not ("instagram.com" in url or "youtu" in url):
        await update.message.reply_text("Пожалуйста, пришли ссылку с Instagram или YouTube.")
        return

    # await update.message.reply_text("Скачиваю видео, подожди немного...")

    ydl_opts = {
        "format": "best",
        "outtmpl": "video.%(ext)s",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as f:
            await update.message.reply_video(video=f)

        os.remove(filename)

    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e)
        logger.error(f"Ошибка при скачивании: {err_msg}")

        # Если ошибка связана с авторизацией/приватностью, сообщаем об этом пользователю
        if ("login required" in err_msg.lower()
            or "private" in err_msg.lower()
            or "rate-limit" in err_msg.lower()
            or "not available" in err_msg.lower()):
            await update.message.reply_text(
                "Видео недоступно для скачивания без авторизации. "
                "Пожалуйста, убедитесь, что видео публичное."
            )
        else:
            await update.message.reply_text(
                "Произошла ошибка при скачивании видео. Попробуйте позже."
            )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r"(instagram\.com|youtu)"),
            handle_video_link,
        )
    )

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )


if __name__ == "__main__":
    main()

