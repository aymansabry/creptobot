# bot.py
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

# ====== Inline Keyboards ======
def _kbd_main():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],
            [InlineKeyboardButton("💰 بدء التداول", callback_data="start_trading"),
             InlineKeyboardButton("🛑 إيقاف التداول", callback_data="stop_trading")],
            [InlineKeyboardButton("📊 حالة السوق", callback_data="market_status"),
             InlineKeyboardButton("📜 التقارير", callback_data="reports")],
        ]
    )

def _kbd_settings():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔑 ربط المنصات", callback_data="link_api")],
            [InlineKeyboardButton("💵 مبلغ الاستثمار", callback_data="set_amount")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")],
        ]
    )

# ====== Command Handlers ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await create_user(user.id)
    await update.message.reply_text(
        "✅ تم التسجيل بنجاح.\nاختر من القائمة:", reply_markup=_kbd_main()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أزرار التحكم:\n"
        "⚙️ الإعدادات — ربط منصة أو تعديل المبلغ\n"
        "💰 بدء التداول — يبدأ البوت باستخدام المبلغ المحفوظ\n"
        "🛑 إيقاف التداول — يوقّف البوت\n"
        "📊 حالة السوق — تحليل OpenAI\n"
        "📜 التقارير — آخر الصفقات المسجلة"
    )

# ====== Callback Query Handler (for inline buttons) ======
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # Settings
    if data == "settings":
        await query.edit_message_text("⚙️ الإعدادات — اختر:", reply_markup=_kbd_settings())
        return

    if data == "back_main":
        await query.edit_message_text("✅ عدت للقائمة الرئيسية.", reply_markup=_kbd_main())
        return

    if data == "link_api":
        context.user_data["stage"] = "api_key"
        await query.edit_message_text("🔑 أرسل الـAPI Key الآن (سطر واحد).")
        return

    if data == "set_amount":
        context.user_data["stage"] = "amount"
        await query.edit_message_text("💵 أرسل مبلغ الاستثمار بالدولار (مثال: 5).")
        return

    # Trading controls
    if data == "start_trading":
        amount = get_amount(user_id)
        if not amount:
            await query.edit_message_text("❌ لم تحدد مبلغًا بعد. اذهب للإعدادات > مبلغ الاستثمار.")
            return
        await query.edit_message_text(f"💰 جاري بدء التداول بالمبلغ: {amount} USDT\n(سأعلمك بالنتائج)")
        asyncio.create_task(start_arbitrage(user_id))
        return

    if data == "stop_trading":
        await stop_arbitrage(user_id)
        await query.edit_message_text("🛑 تم إيقاف التداول.")
        return

    # Market Status
    if data == "market_status":
        await query.edit_message_text("⏳ جاري تحليل السوق، انتظر لحظة...")
        try:
            client = await get_client_for_user(user_id)
        except ValueError:
            await query.edit_message_text("❌ لم تسجل مفاتيح Binance بعد. اذهب للإعدادات.")
            return

        tickers = await client.get_all_tickers()
        sample = ", ".join([t["symbol"] for t in tickers[:40]])
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(None, lambda: ai.analyze({"sample_symbols": sample}))
        chunks = [analysis[i:i+800] for i in range(0, len(analysis), 800)]
        for ch in chunks:
            await query.message.reply_text(f"📊 نصيحة OpenAI:\n{ch}")
        await query.message.reply_text("✅ انتهى التحليل.", reply_markup=_kbd_main())
        return

    # Reports
    if data == "reports":
        trades = get_last_trades(user_id)
        if not trades:
            await query.edit_message_text("📜 لا توجد صفقات مسجلة بعد.", reply_markup=_kbd_main())
            return
        text = "📜 آخر الصفقات:\n"
        for t in trades[:10]:
            ts = getattr(t, "timestamp", None)
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ""
            text += f"• {t.pair} | ربح: {t.profit:.6f}$ | {ts_str}\n"
        await query.edit_message_text(text, reply_markup=_kbd_main())
        return

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
            await update.message.reply_text("✅ تم حفظ المفاتيح بنجاح.", reply_markup=_kbd_main())
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حفظ المفاتيح: {e}", reply_markup=_kbd_main())
        context.user_data["stage"] = None
        return

    if stage == "amount":
        try:
            val = float(text)
            if val <= 0:
                raise ValueError("المبلغ يجب أن يكون أكبر من 0")
            if val > 10000:
                await update.message.reply_text("⚠️ الحد الأقصى للاستثمار 10000 USDT.", reply_markup=_kbd_main())
                context.user_data["stage"] = None
                return
            await save_amount(user_id, val)
            await update.message.reply_text(f"✅ تم حفظ المبلغ: {val} USDT", reply_markup=_kbd_main())
        except Exception:
            await update.message.reply_text("❌ ادخل مبلغاً صالحاً (مثل: 5).", reply_markup=_kbd_main())
        context.user_data["stage"] = None
        return

    await update.message.reply_text("📌 استخدم الأزرار أو اكتب /help لعرض الأوامر.", reply_markup=_kbd_main())

# ====== Main runner ======
def main():
    if not BOT_TOKEN:
        raise ValueError("⚠️ لم يتم العثور على TELEGRAM_BOT_TOKEN في المتغيرات البيئية")

    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🤖 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
