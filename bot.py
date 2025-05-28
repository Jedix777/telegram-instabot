import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на Instagram-видео, и я попробую его скачать.")

# Обработка ссылки Instagram
async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        await update.message.reply_text("Пожалуйста, пришли корректную ссылку на Instagram.")
        return

    await update.message.reply_text("Скачиваю видео, подожди немного...")

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True,
            'cookies': 'cookies.txt',  # Используем файл cookies
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as f:
            await update.message.reply_video(video=f)

        os.remove(filename)

    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        await update.message.reply_text("Не удалось скачать видео 😢 Убедитесь, что ссылка рабочая, а куки актуальны.")

# Главная функция
def main():
    logger.info("Запускаю бота...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_link))

    app.run_polling()

if __name__ == "__main__":
    main()

