import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from db import get_user, create_user, save_api_keys, save_amount, get_amount, get_market_summary
from openai_integration import get_market_advice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAIN_MENU = [["⚙️ الإعدادات", "💰 بدء التداول"], ["🛑 إيقاف التداول", "📊 حالة السوق"], ["📜 التقارير"]]
SETTINGS_MENU = [["🔑 ربط المنصات", "💵 مبلغ الاستثمار"], ["⬅️ رجوع"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await create_user(update.effective_chat.id, update.effective_user.username)
    await update.message.reply_text(
        "✅ تم التسجيل بنجاح، افتح الإعدادات لإضافة مفاتيح Binance والمبلغ.",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(SETTINGS_MENU, resize_keyboard=True)
    )

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔑 ربط المنصات":
        context.user_data['setting_stage'] = 'api_key'
        await update.message.reply_text("أرسل الـAPI Key:")
    elif text == "💵 مبلغ الاستثمار":
        context.user_data['setting_stage'] = 'amount'
        await update.message.reply_text("أرسل مبلغ الاستثمار بالدولار (يمكن تغييره لاحقاً):")
    elif text == "⬅️ رجوع":
        await update.message.reply_text(
            "✅ عدت للقائمة الرئيسية.",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    stage = context.user_data.get('setting_stage')
    if stage == 'api_key':
        context.user_data['api_key'] = update.message.text
        context.user_data['setting_stage'] = 'api_secret'
        await update.message.reply_text("أرسل الـAPI Secret:")
    elif stage == 'api_secret':
        context.user_data['api_secret'] = update.message.text
        success = await save_api_keys(user_id, context.user_data['api_key'], context.user_data['api_secret'])
        if success:
            await update.message.reply_text("✅ تم ربط المنصة بنجاح.")
        else:
            await update.message.reply_text("❌ المفاتيح غير صحيحة، حاول مرة أخرى.")
        context.user_data['setting_stage'] = None
    elif stage == 'amount':
        try:
            amount = float(update.message.text)
            await save_amount(user_id, amount)
            await update.message.reply_text(f"✅ تم حفظ المبلغ: {amount} USDT")
        except ValueError:
            await update.message.reply_text("❌ الرجاء إدخال رقم صحيح.")
        context.user_data['setting_stage'] = None
    else:
        await update.message.reply_text("✅ استخدم القوائم لاختيار الخيارات.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    summary, rejected = await get_market_summary(user_id)
    advice = await get_market_advice()
    # إرسال الرسائل على أجزاء
    await update.message.reply_text(f"📊 ملخص السوق:\nعدد الأزواج المتاحة: {summary['total']}\nقابلة للتداول: {summary['trading']}")
    if rejected:
        text = "❌ الأزواج المرفوضة:\n" + "\n".join([f"{p['symbol']}: {p['reason']}" for p in rejected])
        await update.message.reply_text(text)
    await update.message.reply_text(f"💡 نصائح السوق:\n{advice}")
    await update.message.reply_text("✅ جاهز للتداول.")

async def start_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    amount = await get_amount(user_id)
    if amount:
        await update.message.reply_text(f"💰 بدأ التداول بمبلغ: {amount} USDT")
        # هنا يبدأ البوت تداول حقيقي حسب المفاتيح والمبلغ
    else:
        await update.message.reply_text("❌ لم يتم تحديد مبلغ الاستثمار بعد.")

async def stop_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    # هنا ايقاف التداول
    await update.message.reply_text("🛑 تم إيقاف التداول.")

if __name__ == "__main__":
    app = ApplicationBuilder().token("TELEGRAM_BOT_TOKEN").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Regex("^⚙️ الإعدادات$"), settings))
    app.add_handler(MessageHandler(filters.Regex("^💰 بدء التداول$"), start_trading))
    app.add_handler(MessageHandler(filters.Regex("^🛑 إيقاف التداول$"), stop_trading))
    app.add_handler(MessageHandler(filters.Regex("^📊 حالة السوق$"), market))
    app.add_handler(MessageHandler(filters.Regex("^📜 التقارير$"), lambda u,c: c.bot.send_message(u.effective_chat.id,"لا توجد صفقات بعد.")))
    app.run_polling()
