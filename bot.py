import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os
from trading import start_arbitrage, stop_arbitrage

# إعداد اللوج
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# متغير البيئة
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ====== Handlers ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("▶️ بدء المراجحة", callback_data="start")],
        [InlineKeyboardButton("⏹ إيقاف المراجحة", callback_data="stop")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحباً! أنا بوت المراجحة 🤖", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("استخدم الأزرار للتحكم في البوت.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start":
        await query.edit_message_text("🚀 بدأنا المراجحة...")
        await start_arbitrage()
    elif query.data == "stop":
        await query.edit_message_text("🛑 تم إيقاف المراجحة.")
        await stop_arbitrage()


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 استخدم الأزرار للتحكم في البوت.")


# ====== Main ======
def main():
    if not BOT_TOKEN:
        raise ValueError("⚠️ لم يتم العثور على TELEGRAM_BOT_TOKEN في المتغيرات البيئية")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🤖 البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
