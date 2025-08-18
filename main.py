import logging
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    Application
)
from config import Config
from user_manager import UserManager
from trading_engine import TradingEngine
import re

# إعدادات التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    """إرسال رسالة ترحيبية"""
    user = update.effective_user
    await update.message.reply_html(
        f"مرحباً {user.mention_html()}! 👋\n\n"
        "🔹 هذا البوت يساعدك في التداول الآلي على Binance\n"
        "🔹 استخدم /help لعرض الأوامر المتاحة"
    )

async def help_command(update: Update, context: CallbackContext):
    """عرض الأوامر المتاحة"""
    await update.message.reply_text(
        "📋 الأوامر المتاحة:\n\n"
        "/start - بدء استخدام البوت\n"
        "/help - عرض هذه المساعدة\n"
        "/set_api [API_KEY] [SECRET_KEY] - إضافة مفاتيح Binance\n"
        "/buy [SYMBOL] [AMOUNT_USDT] - شراء عملة\n"
        "/sell [SYMBOL] [AMOUNT_USDT] - بيع عملة"
    )

async def set_api(update: Update, context: CallbackContext):
    """حفظ مفاتيح API"""
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) != 2:
        await update.message.reply_text("⚠️ يرجى إدخال المفاتيح بشكل صحيح:\n/set_api API_KEY SECRET_KEY")
        return
    
    api_key, api_secret = args
    user_manager = UserManager()
    if user_manager.update_user_credentials(user_id, api_key, api_secret):
        await update.message.reply_text("✅ تم حفظ مفاتيح API بنجاح!")
    else:
        await update.message.reply_text("❌ فشل في حفظ المفاتيح!")

async def execute_trade(update: Update, context: CallbackContext, side: str):
    """تنفيذ عملية تداول"""
    user_id = update.effective_user.id
    try:
        symbol = context.args[0].upper()
        amount = float(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text(f"⚠️ يرجى إدخال البيانات بشكل صحيح:\n/{side.lower()} SYMBOL AMOUNT")
        return
    
    try:
        engine = TradingEngine(user_id)
        order = await engine.execute_order(symbol, side, amount)
        await update.message.reply_text(f"✅ تم تنفيذ {side} لـ {symbol} بمبلغ {amount} USDT")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")

async def buy(update: Update, context: CallbackContext):
    """معالج أمر الشراء"""
    await execute_trade(update, context, "BUY")

async def sell(update: Update, context: CallbackContext):
    """معالج أمر البيع"""
    await execute_trade(update, context, "SELL")

async def error_handler(update: Update, context: CallbackContext):
    """معالجة الأخطاء"""
    logger.error(f"حدث خطأ: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ حدث خطأ غير متوقع!")

def main():
    """بدء تشغيل البوت"""
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_api", set_api))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("sell", sell))
    
    # معالجة الأخطاء
    application.add_error_handler(error_handler)
    
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()