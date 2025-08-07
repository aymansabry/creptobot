from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

def setup_user_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    keyboard = [
        [KeyboardButton("🚀 بدء التداول")],
        [KeyboardButton("ℹ️ معلومات")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(f"👋 أهلاً {user.first_name}! مرحبًا بك في بوت التداول.\nاختر من القائمة:", reply_markup=reply_markup)

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "🚀 بدء التداول":
        context.bot_data["trading_active"] = True
        await update.message.reply_text("✅ تم تفعيل التداول لحسابك.")
    elif text == "ℹ️ معلومات":
        await update.message.reply_text("🤖 هذا البوت يقوم بالتداول التلقائي باستخدام الذكاء الاصطناعي.\nيتم تنفيذ صفقات المراجحة بناءً على التحليلات اللحظية.")
    else:
        await update.message.reply_text("❓ لم أفهم طلبك. الرجاء اختيار أمر من القائمة.")