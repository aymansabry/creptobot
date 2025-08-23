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

# دوال وموديولات المشروع (تأكد الملفات موجودة كما اتفقنا)
from db import create_user, save_api_keys, get_user_api_keys, save_amount, get_amount, get_last_trades
from trading import start_arbitrage, stop_arbitrage, get_client  # start_arbitrage(user_id), stop_arbitrage()
from ai_strategy import AIStrategy
from datetime import datetime

# إعداد اللوج
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ai = AIStrategy()

# ====== مساعدة داخلية ======
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

# ====== Handlers ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await create_user(user.id, user.username or "")
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

# زرار الـ Inline keyboard
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # إعدادات
    if data == "settings":
        await query.edit_message_text("⚙️ الإعدادات — اختر:", reply_markup=_kbd_settings())
        return

    if data == "back_main":
        await query.edit_message_text("✅ عدت للقائمة الرئيسية.", reply_markup=_kbd_main())
        return

    if data == "link_api":
        # ندخل المستخدم في وضع إدخال الـ API key ثم secret
        context.user_data["stage"] = "api_key"
        await query.edit_message_text("🔑 أرسل الـAPI Key الآن (سطر واحد).")
        return

    if data == "set_amount":
        # وضع إدخال المبلغ
        context.user_data["stage"] = "amount"
        await query.edit_message_text("💵 أرسل مبلغ الاستثمار بالدولار (مثال: 5).")
        return

    # بدء / إيقاف التداول
    if data == "start_trading":
        # تشغيل في مهمة فرعية حتى لا يعرقل البوت
        amount = await get_amount(user_id)
        if not amount:
            await query.edit_message_text("❌ لم تحدد مبلغًا بعد. اذهب للإعدادات > مبلغ الاستثمار.")
            return
        await query.edit_message_text(f"💰 جاري بدء التداول بالمبلغ: {amount} USDT\n(سأعلمك بالنتائج)")
        # تشغيل المهمة بشكل غير متزامن
        asyncio.create_task(start_arbitrage(user_id))
        return

    if data == "stop_trading":
        await stop_arbitrage()
        await query.edit_message_text("🛑 تم إيقاف التداول.")
        return

    # حالة السوق -> سنجلب تحليل من OpenAI (في thread لأن analyze قد يكون blocking)
    if data == "market_status":
        await query.edit_message_text("⏳ جاري تحليل السوق، انتظر لحظة...")
        # اجمع بيانات بسيطة (مثال: أزواج مختارة أو آخر أسعار)
        try:
            client = await get_client(user_id)  # للتأكد من مفاتيح المستخدم
        except Exception:
            await query.edit_message_text("❌ لم تسجل مفاتيح Binance بعد. اذهب للإعدادات.")
            return

        # مثال: زود بيانات مبسطة لـ OpenAI
        tickers = await client.get_all_tickers()
        # نختصر لأكبر الأزواج (بسبب طول النص)
        sample = ", ".join([t["symbol"] for t in tickers[:40]])
        # شغّل تحليل OpenAI في executor لتفادي حظر loop
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(None, lambda: ai.analyze({"sample_symbols": sample}))
        # نقسم الرد على رسائل صغيرة لو طويل
        chunks = [analysis[i:i+800] for i in range(0, len(analysis), 800)]
        for ch in chunks:
            await query.message.reply_text(f"📊 نصيحة OpenAI:\n{ch}")
        await query.message.reply_text("✅ انتهى التحليل.")
        return

    # تقارير
    if data == "reports":
        trades = get_last_trades()
        if not trades:
            await query.edit_message_text("📜 لا توجد صفقات مسجلة بعد.")
            return
        # صياغة بسيطة
        text = "📜 آخر الصفقات:\n"
        for t in trades[:10]:
            # t.pair, t.profit, t.timestamp حسب جدولك
            ts = getattr(t, "timestamp", None)
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ""
            text += f"• {t.pair} | ربح: {t.profit:.6f}$ | {ts_str}\n"
        await query.edit_message_text(text)
        return

# استقبال الرسائل — نعالج إدخال المفاتيح أو المبلغ اعتمادًا على الـ stage
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    stage = context.user_data.get("stage")

    # مرحلة إدخال API Key ثم Secret
    if stage == "api_key":
        context.user_data["tmp_api_key"] = text
        context.user_data["stage"] = "api_secret"
        await update.message.reply_text("🗝️ الآن أرسل الـAPI Secret:")
        return

    if stage == "api_secret":
        api_key = context.user_data.pop("tmp_api_key", None)
        api_secret = text
        # سنحاول حفظ المفاتيح والتحقق منها عبر محاولة إنشاء client
        try:
            # حفظ أوليًا (DB)
            await save_api_keys(user_id, api_key, api_secret)
            # تحقق عملي: حاول إنشاء عميل Binance والتحقق من الحساب
            try:
                client = await get_client(user_id)
                # اختبار بسيط لجلب الحساب
                await client.get_account()  # سيؤكد صلاحية المفاتيح
                await update.message.reply_text("✅ تم التحقق من المفاتيح وحفظها بنجاح.")
            except Exception as e:
                # إذا فشل، نحذف المفاتيح المحفوظة ونبلغ المستخدم
                await save_api_keys(user_id, None, None)
                await update.message.reply_text(f"❌ التحقق فشل: {e}\nتأكد من صلاحية المفاتيح وصلاحية التداول.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حفظ المفاتيح: {e}")
        context.user_data["stage"] = None
        return

    # مرحلة إدخال المبلغ
    if stage == "amount":
        try:
            val = float(text)
            if val <= 0:
                raise ValueError("المبلغ يجب أن يكون أكبر من 0")
            # حد أقصى استثمار كما قلت قبل: 10000
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

    # استقبال مفاتيح/مبلغ بشكل CSV مباشر (fallback)
    if "," in text and len(text.split(",")) == 2:
        api_key, api_secret = text.split(",", 1)
        await save_api_keys(user_id, api_key.strip(), api_secret.strip())
        await update.message.reply_text("✅ تم حفظ المفاتيح (أدخل /start أو افتح القائمة).")
        return

    # أو أي رسالة عامة
    await update.message.reply_text("📌 استخدم الأزرار أو اكتب /help لعرض الأوامر.")

# ====== Main runner (غير async لتفادي مشاكل event loop) ======
def main():
    if not BOT_TOKEN:
        raise ValueError("⚠️ لم يتم العثور على TELEGRAM_BOT_TOKEN في المتغيرات البيئية")

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands & Callbacks
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🤖 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
