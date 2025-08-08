from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

def setup_user_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("🚀 بدء التداول"), KeyboardButton("ℹ️ معلومات")],
        [KeyboardButton("💼 محفظتي"), KeyboardButton("📊 الرصيد")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("مرحبًا بك في بوت التداول الذكي 👋\nاختر من القائمة:", reply_markup=reply_markup)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🚀 بدء التداول":
        await update.message.reply_text("🟢 تم تفعيل التداول الفعلي لحسابك.")
        # يمكنك هنا استدعاء التداول الحقيقي مثلاً:
        # executor = context.bot_data["trade_executor"]
        # await executor.execute_trade_for_user(user_id, ...)
    elif text == "ℹ️ معلومات":
        await update.message.reply_text("🤖 هذا بوت تداول آلي مدعوم بالذكاء الاصطناعي يعمل بشكل ذاتي بالكامل.")
    elif text == "💼 محفظتي":
        await update.message.reply_text("📁 يتم العمل على عرض بيانات محفظتك قريبًا.")
    elif text == "📊 الرصيد":
        await update.message.reply_text("💰 سيتم إظهار الرصيد الحقيقي لاحقًا.")
    else:
        await update.message.reply_text("❓ لم أفهم الأمر، الرجاء استخدام الأزرار.")