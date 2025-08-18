import logging
from telegram import Update, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
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

# تهيئة البوت
bot = Bot(token=Config.TELEGRAM_TOKEN)
user_manager = UserManager()

def start(update: Update, context: CallbackContext):
    """إرسال رسالة ترحيبية عند استخدام الأمر /start"""
    user = update.effective_user
    welcome_msg = f"""
مرحباً {user.mention_html()}! 👋

🔹 هذا البوت يساعدك في التداول الآلي على Binance
🔹 استخدم /help لعرض الأوامر المتاحة

📌 قم بإعداد مفاتيح API أولاً باستخدام:
/set_api [API_KEY] [SECRET_KEY]
    """
    update.message.reply_html(welcome_msg)

def help_command(update: Update, context: CallbackContext):
    """عرض جميع الأوامر المتاحة"""
    help_text = """
📋 <b>الأوامر المتاحة:</b>

🔹 /start - بدء استخدام البوت
🔹 /help - عرض هذه المساعدة
🔹 /set_api [API_KEY] [SECRET_KEY] - إضافة مفاتيح Binance
🔹 /buy [SYMBOL] [AMOUNT_USDT] - شراء عملة
🔹 /sell [SYMBOL] [AMOUNT_USDT] - بيع عملة
🔹 /set_percent [PERCENT] - تعيين نسبة التداول

📌 <i>مثال:</i> /buy BTCUSDT 100
    """
    update.message.reply_html(help_text)

def set_api(update: Update, context: CallbackContext):
    """حفظ مفاتيح API للمستخدم"""
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) != 2:
        update.message.reply_text(
            "⚠️ يرجى إدخال المفاتيح بشكل صحيح:\n"
            "/set_api API_KEY SECRET_KEY"
        )
        return
    
    api_key, api_secret = args
    if user_manager.update_user_credentials(user_id, api_key, api_secret):
        update.message.reply_text(
            "✅ تم حفظ مفاتيح API بنجاح!\n"
            "يمكنك الآن البدء في التداول."
        )
    else:
        update.message.reply_text(
            "❌ فشل في حفظ المفاتيح! يرجى المحاولة لاحقاً."
        )

def set_trade_percent(update: Update, context: CallbackContext):
    """تعيين نسبة التداول"""
    user_id = update.effective_user.id
    try:
        percent = float(context.args[0])
        if not (0.1 <= percent <= 100):
            raise ValueError
    except (IndexError, ValueError):
        update.message.reply_text(
            "⚠️ يرجى إدخال نسبة صحيحة بين 0.1 و 100\n"
            "مثال: /set_percent 2.5"
        )
        return
    
    try:
        user_manager.update_trade_percent(user_id, percent)
        update.message.reply_text(f"✅ تم تعيين نسبة التداول إلى {percent}%")
    except Exception as e:
        logger.error(f"Failed to set percent for {user_id}: {str(e)}")
        update.message.reply_text("❌ فشل في تحديث النسبة! يرجى المحاولة لاحقاً.")

def execute_trade(update: Update, context: CallbackContext, side: str):
    """تنفيذ عملية تداول (شراء/بيع)"""
    user_id = update.effective_user.id
    try:
        symbol = context.args[0].upper()
        amount = float(context.args[1])
    except (IndexError, ValueError):
        update.message.reply_text(
            f"⚠️ يرجى إدخال البيانات بشكل صحيح:\n"
            f"/{side.lower()} SYMBOL AMOUNT\n"
            f"مثال: /{side.lower()} BTCUSDT 100"
        )
        return
    
    # التحقق من صيغة الرمز (مثل BTCUSDT)
    if not re.match(r"^[A-Z]{6,12}$", symbol):
        update.message.reply_text("❌ رمز التداول غير صحيح!")
        return
    
    try:
        engine = TradingEngine(user_id)
        order = engine.execute_order(symbol, side, amount)
        
        if order:
            msg = (
                f"✅ تم تنفيذ {side} بنجاح!\n"
                f"الرمز: {symbol}\n"
                f"المبلغ: {amount:.2f} USDT\n"
                f"الكمية: {float(order['executedQty']):.6f}"
            )
            update.message.reply_text(msg)
        else:
            update.message.reply_text("❌ فشل في تنفيذ الأمر! يرجى التحقق من المفاتيح والرصيد.")
    except Exception as e:
        logger.error(f"Trade error for {user_id}: {str(e)}")
        update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

def buy(update: Update, context: CallbackContext):
    """معالج أمر الشراء"""
    execute_trade(update, context, "BUY")

def sell(update: Update, context: CallbackContext):
    """معالج أمر البيع"""
    execute_trade(update, context, "SELL")

def error_handler(update: Update, context: CallbackContext):
    """معالجة الأخطاء العامة"""
    logger.error(f"Error: {context.error}", exc_info=context.error)
    if update and update.effective_message:
        update.effective_message.reply_text(
            "❌ حدث خطأ غير متوقع! يرجى المحاولة لاحقاً."
        )

def main():
    """بدء تشغيل البوت"""
    updater = Updater(bot=bot, use_context=True)
    dp = updater.dispatcher

    # إضافة معالجات الأوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("set_api", set_api))
    dp.add_handler(CommandHandler("set_percent", set_trade_percent))
    dp.add_handler(CommandHandler("buy", buy))
    dp.add_handler(CommandHandler("sell", sell))

    # معالجة الأخطاء
    dp.add_error_handler(error_handler)

    # بدء الاستماع للتحديثات
    updater.start_polling()
    logger.info("Bot is running...")
    updater.idle()

if __name__ == "__main__":
    main()