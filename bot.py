
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Отправь мне ссылку на видео или Reels из Instagram.')

async def download_instagram_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id

    if 'instagram.com' not in url:
        await update.message.reply_text('Пожалуйста, отправьте ссылку на Instagram.')
        return

    ydl_opts = {
        'outtmpl': 'downloaded_video.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True,
    }

    try:
        await update.message.reply_text('🔄 Загружаю видео...')
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open('downloaded_video.mp4', 'rb') as video:
            await context.bot.send_video(chat_id=chat_id, video=video)

        os.remove('downloaded_video.mp4')

    except Exception as e:
        logger.error(f'Ошибка: {e}')
        await update.message.reply_text('❌ Не удалось скачать видео.')

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram_video))

    print("Бот запущен...")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
