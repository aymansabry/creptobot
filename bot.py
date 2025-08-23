# bot.py
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Imports from other files
from db import create_user, save_api_keys, get_user_api_keys, save_amount, get_amount, get_last_trades
from trading import start_arbitrage, stop_arbitrage, get_client_for_user
from ai_strategy import AIStrategy
from datetime import datetime

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ai = AIStrategy()

# ====== Command Handlers ======
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await create_user(user.id)
    await update.message.reply_text(
        "✅ تم التسجيل بنجاح.\nللحصول على قائمة الأوامر، اكتب /help."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 قائمة الأوامر المتاحة:\n"
        "• /start — بدء البوت والبدء في استخدامه\n"
        "• /settings — إعدادات البوت (مفاتيح API ومبلغ الاستثمار)\n"
        "• /start_trading — بدء التداول باستخدام المبلغ المحفوظ\n"
        "• /stop_trading — إيقاف التداول\n"
        "• /market_status — تحليل حالة السوق بواسطة الذكاء الاصطناعي\n"
        "• /reports — عرض آخر الصفقات المسجلة"
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ الإعدادات — اختر:\n"
        "1. اكتب **Link API** لربط مفاتيح منصات التداول.\n"
        "2. اكتب **Set Amount** لضبط مبلغ الاستثمار."
    )

async def start_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    amount = get_amount(user_id)
    if not amount:
        await update.message.reply_text("❌ لم تحدد مبلغًا بعد. اذهب للإعدادات واكتب **Set Amount**.")
        return
    await update.message.reply_text(f"💰 جاري بدء التداول بالمبلغ: {amount} USDT\n(سأعلمك بالنتائج)")
    asyncio.create_task(start_arbitrage(user_id))

async def stop_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await stop_arbitrage(user_id)
    await update.message.reply_text("🛑 تم إيقاف التداول.")

async def market_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("⏳ جاري تحليل السوق، انتظر لحظة...")
    try:
        client = await get_client_for_user(user_id)
    except ValueError:
        await update.message.reply_text("❌ لم تسجل مفاتيح Binance بعد. اذهب للإعدادات واكتب **Link API**.")
        return

    tickers = await client.get_all_tickers()
    sample = ", ".join([t["symbol"] for t in tickers[:40]])
    analysis = await asyncio.to_thread(lambda: ai.analyze({"sample_symbols": sample}))
    chunks = [analysis[i:i+800] for i in range(0, len(analysis), 800)]
    for ch in chunks:
        await update.message.reply_text(f"📊 نصيحة OpenAI:\n{ch}")
    await update.message.reply_text("✅ انتهى التحليل.")

async def reports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    trades = get_last_trades(user_id)
    if not trades:
        await update.message.reply_text("📜 لا توجد صفقات مسجلة بعد.")
        return
    text = "📜 آخر الصفقات:\n"
    for t in trades[:10]:
        ts = getattr(t, "timestamp", None)
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ""
        text += f"• {t.pair} | ربح: {t.profit:.6f}$ | {ts_str}\n"
    await update.message.reply_text(text)

# ====== Message Handler (for text input) ======
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    stage = context.user_data.get("stage")

    if stage == "api_key":
        context.user_data["tmp_api_key"] = text
        context.user_data["stage"] = "api_secret"
        await update.message.reply_text("🗝️ الآن أرسل الـAPI Secret:")
        return

    if stage == "api_secret":
        api_key = context.user_data.pop("tmp_api_key", None)
        api_secret = text
        try:
            await save_api_keys(user_id, api_key, api_secret)
            await update.message.reply_text("✅ تم حفظ المفاتيح بنجاح.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حفظ المفاتيح: {e}")
        context.user_data["stage"] = None
        return

    if stage == "amount":
        try:
            val = float(text)
            if val <= 0:
                raise ValueError("المبلغ يجب أن يكون أكبر من 0")
            if val > 10000:
                await update.message.reply_text("⚠️ الحد الأقصى للاستثمار 10000 USDT.")
                context.user_data["stage"] = None
                return
            await save_amount(user_id, val)
            await update.message.reply_text(f"✅ تم حفظ المبلغ: {val} USDT")
        except Exception:
            await update.message.reply_text("❌ ادخل مبلغاً صالحاً (مثل: 5).")
        context.user_data["stage"] = None
        return
    
    # Handle text commands
    if text.lower() == "link api":
        context.user_data["stage"] = "api_key"
        await update.message.reply_text("🔑 أرسل الـAPI Key الآن (سطر واحد).")
        return
    
    if text.lower() == "set amount":
        context.user_data["stage"] = "amount"
        await update.message.reply_text("💵 أرسل مبلغ الاستثمار بالدولار (مثال: 5).")
        return

    await update.message.reply_text("📌 استخدم قائمة الأوامر أو اكتب /help.")

# ====== Main runner ======
def main():
    if not BOT_TOKEN:
        raise ValueError("⚠️ لم يتم العثور على TELEGRAM_BOT_TOKEN في المتغيرات البيئية")

    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers for commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("start_trading", start_trading_command))
    app.add_handler(CommandHandler("stop_trading", stop_trading_command))
    app.add_handler(CommandHandler("market_status", market_status_command))
    app.add_handler(CommandHandler("reports", reports_command))
    
    # Add handler for text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🤖 البوت يعمل الآن...")
    app.run_polling(poll_interval=1.0)

if __name__ == "__main__":
    main()
