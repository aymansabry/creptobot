import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from db import create_user, save_api_keys, save_amount, get_amount
from trading import start_arbitrage, stop_arbitrage
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAIN_MENU = [["⚙️ الإعدادات", "💰 بدء التداول"], ["🛑 إيقاف التداول", "📊 حالة السوق"], ["📜 التقارير"]]
SETTINGS_MENU = [["🔑 ربط المنصات", "💵 مبلغ الاستثمار"], ["⬅️ رجوع"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await create_user(update.effective_chat.id, update.effective_user.username)
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
        context.user_data['stage'] = 'api_key'
        await update.message.reply_text("أرسل الـAPI Key:")
    elif text == "💵 مبلغ الاستثمار":
        context.user_data['stage'] = 'amount'
        await update.message.reply_text("أرسل مبلغ الاستثمار بالدولار:")
    elif text == "⬅️ رجوع":
        await update.message.reply_text("✅ عدت للقائمة الرئيسية.",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get('stage')
    user_id = update.effective_chat.id
    if stage == 'api_key':
        context.user_data['api_key'] = update.message.text
        context.user_data['stage'] = 'api_secret'
        await update.message.reply_text("أرسل الـAPI Secret:")
    elif stage == 'api_secret':
        api_key = context.user_data.get('api_key')
        api_secret = update.message.text
        await save_api_keys(user_id, api_key, api_secret)
        await update.message.reply_text("✅ تم ربط المنصة بنجاح.")
        context.user_data['stage'] = None
    elif stage == 'amount':
        try:
            amount = float(update.message.text)
            await save_amount(user_id, amount)
            await update.message.reply_text(f"✅ تم حفظ المبلغ: {amount} USDT")
        except:
            await update.message.reply_text("❌ المبلغ غير صحيح، أرسل رقم بالدولار.")
        context.user_data['stage'] = None

async def start_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    amount = await get_amount(user_id)
    if not amount:
        await update.message.reply_text("❌ الرجاء تحديد مبلغ الاستثمار أولاً في الإعدادات.")
        return
    await update.message.reply_text(f"💰 بدء التداول بالمبلغ: {amount} USDT")
    asyncio.create_task(start_arbitrage(user_id))

async def stop_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop_arbitrage()
    await update.message.reply_text("🛑 تم إيقاف التداول.")

async def main():
    app = ApplicationBuilder().token("TELEGRAM_BOT_TOKEN_HERE").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Regex("⚙️ الإعدادات"), settings))
    app.add_handler(MessageHandler(filters.Regex("💰 بدء التداول"), start_trading))
    app.add_handler(MessageHandler(filters.Regex("🛑 إيقاف التداول"), stop_trading))
    # باقي القوائم يمكنك إضافة handlers للتقارير وحالة السوق
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
