import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from db import create_user, save_api_keys, get_user_api_keys, save_amount, get_amount
from trading import start_arbitrage, stop_arbitrage
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- دالة start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    await create_user(user_id, username)
    
    keyboard = [
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],
        [InlineKeyboardButton("💰 بدء التداول", callback_data="start_trading")],
        [InlineKeyboardButton("🛑 إيقاف التداول", callback_data="stop_trading")],
        [InlineKeyboardButton("📊 حالة السوق", callback_data="market_status")],
        [InlineKeyboardButton("📜 التقارير", callback_data="reports")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ أهلاً! اختر من القائمة:", reply_markup=reply_markup)

# --- التعامل مع الأزرار ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "settings":
        await query.message.reply_text(
            "أرسل مفاتيح Binance بهذا الشكل (CSV):\nAPI_KEY,API_SECRET\nأو 'skip' للرجوع."
        )
    elif query.data == "start_trading":
        try:
            await start_arbitrage(user_id)
            await query.message.reply_text("💰 التداول بدأ.")
        except Exception as e:
            await query.message.reply_text(f"❌ فشل بدء التداول: {e}")
    elif query.data == "stop_trading":
        await stop_arbitrage()
        await query.message.reply_text("🛑 التداول تم إيقافه.")
    elif query.data == "market_status":
        api_keys = await get_user_api_keys(user_id)
        if not api_keys:
            await query.message.reply_text("❌ لم يتم تسجيل مفاتيح Binance بعد.")
            return
        client = await start_arbitrage.get_client(user_id)  # إعادة استخدام client
        tickers = await client.get_all_tickers()
        msg = f"ملخص السوق: عدد أزواج محمّلة: {len(tickers)}"
        await query.message.reply_text(msg)
    elif query.data == "reports":
        await query.message.reply_text("لا توجد صفقات بعد.")

# --- استقبال الرسائل العادية ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # استقبال مفاتيح Binance
    if "," in text:
        try:
            api_key, api_secret = text.strip().split(",")
            await save_api_keys(user_id, api_key, api_secret)
            await update.message.reply_text("✅ تم حفظ مفاتيح Binance.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حفظ المفاتيح: {e}")
    elif text.lower() == "skip":
        await update.message.reply_text("تم الرجوع للقائمة الرئيسية.")
    else:
        await update.message.reply_text("✅ البوت شغال! استخدم القوائم للتفاعل.")

# --- تشغيل البوت ---
async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(app.builder.message_handler(message_handler))

    print("✅ البوت شغال!")
    await app.run_polling()
