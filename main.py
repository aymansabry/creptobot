import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from core.config import config
from menus.user import main_menu, trading_menu, wallet_menu
import handlers.user.trading_handlers as trading_handlers

# ... (بقية الإعدادات)

def setup_handlers(application):
    # معالجات الأوامر
    application.add_handler(CommandHandler("start", main_menu.show_main_menu))
    
    # معالجات القوائم
    application.add_handler(MessageHandler(filters.Text(["💰 استثمار جديد"]), trading_menu.show_new_investment))
    application.add_handler(MessageHandler(filters.Text(["📊 تحليل السوق"]), trading_handlers.analyze_market))
    application.add_handler(MessageHandler(filters.Text(["💼 محفظتي"]), wallet_menu.show_wallet))
    
    # معالجات أخرى
    application.add_handler(CallbackQueryHandler(trading_handlers.handle_investment_callback, pattern="^invest_"))

def main():
    if not config.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN غير مضبوط!")
        return

    try:
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()
        setup_handlers(application)
        
        logger.info("🤖 جاري تشغيل البوت...")
        application.run_polling()
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {str(e)}")
