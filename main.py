from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import Config
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ البوت يعمل بنجاح\n"
        f"نسبة التداول: {Config.BOT_PERCENT}%\n"
        f"حدود الاستثمار: {Config.MIN_INVEST}-{Config.MAX_INVEST} USDT"
    )

def main():
    app = Application.builder().token(Config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()