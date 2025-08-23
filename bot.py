import os
import asyncio
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
from trading import start_arbitrage, stop_arbitrage

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# المتغيرات البيئية
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# --------- أوامر البوت ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("▶️ تشغيل المراجحة", callback_data="start"),
            InlineKeyboardButton("⏹ إيقاف", callback_data="stop"),
        ],
        [InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("أهلاً! 👋\nاختر أمر:", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 الأوامر المتاحة:\n"
        "/start - القائمة الرئيسية\n"
        "▶️ تشغيل المراجحة\n"
        "⏹ إيقاف\n"
        "ℹ️ مساعدة"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start":
        await query.edit_message_text("🚀 تم تشغيل بوت المراجحة")
        asyncio.create_task(start_arbitrage())
    elif query.data == "stop":
        await query.edit_message_text("🛑 تم إيقاف بوت المراجحة")
        await stop_arbitrage()
    elif query.data == "help":
        await query.edit_message_text(
            "📖 الأوامر المتاحة:\n"
            "/start - القائمة الرئيسية\n"
            "▶️ تشغيل المراجحة\n"
            "⏹ إيقاف\n"
            "ℹ️ مساعدة"
        )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ استخدم الأزرار أو اكتب /help لعرض المساعدة.")


# --------- تشغيل التطبيق ---------
async def main():
    if not BOT_TOKEN:
        raise ValueError("⚠️ لم يتم العثور على TELEGRAM_BOT_TOKEN في المتغيرات البيئية")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🤖 البوت يعمل الآن...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
