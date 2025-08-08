from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💼 محفظتي":
        await update.message.reply_text("📦 عرض محفظتك...")
    elif text == "📊 الرصيد":
        await update.message.reply_text("💰 رصيدك هو 0.00 USDT")
    elif text == "🤖 بدء التداول":
        await update.message.reply_text("🚀 جاري بدء التداول...")
    elif text == "👤 حسابي":
        await update.message.reply_text("🧾 بيانات حسابك...")
    else:
        await update.message.reply_text("❓ لم أفهم هذا الأمر.")

menu_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu)
