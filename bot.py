import os
import logging
import yt_dlp
from telegram import Update, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Например: https://yourbot.onrender.com
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))  # Замените на свой Telegram user ID

COOKIES_FILE = "cookies.txt"

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь ссылку на Instagram или YouTube видео — я попробую его скачать.")

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return

    if os.path.exists(COOKIES_FILE):
        modified_time = datetime.fromtimestamp(os.path.getmtime(COOKIES_FILE)).strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(f"✅ Файл cookies.txt найден\n📅 Обновлён: {modified_time}")
    else:
        await update.message.reply_text("⚠️ Файл cookies.txt не найден.")

# Загрузка cookies
async def upload_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет прав загружать cookies.")
        return

    doc = update.message.document
    if not doc or not doc.file_name.endswith(".txt"):
        await update.message.reply_text("⚠️ Пожалуйста, загрузите .txt файл cookies.")
        return

    await update.message.chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)

    try:
        file = await doc.get_file()
        await file.download_to_drive(COOKIES_FILE)
        await update.message.reply_text("✅ Cookies успешно обновлены!")
    except Exception as e:
        logger.error(f"Ошибка при загрузке cookies: {e}")
        await update.message.reply_text("❌ Не удалось сохранить файл cookies.")

# Обработка Instagram/YouTube ссылок
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not ("instagram.com" in url or "youtu" in url):
        return  # Игнорировать прочее

    await update.message.chat.send_action(action=ChatAction.UPLOAD_VIDEO)
    await update.message.reply_text("⏳ Скачиваю видео...")

    try:
        ydl_opts = {
            "format": "best",
            "outtmpl": "video.%(ext)s",
            "quiet": True,
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as f:
            await update.message.reply_video(video=f)

        os.remove(filename)

    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        await update.message.reply_text("❌ Не удалось скачать видео. Убедитесь, что ссылка рабочая и cookies актуальны.")

# Главная точка входа
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))

    # Документы (cookies.txt)
    app.add_handler(MessageHandler(filters.Document.ALL, upload_cookies))

    # Обработка ссылок в текстах
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (filters.EntityType.URL | filters.Regex(r"(instagram\.com|youtu)")),
        handle_link
    ))

    # Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()
