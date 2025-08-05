import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config.config import Config
from handlers import (
    user_handlers,
    admin_handlers,
    error_handlers
)
from database.db_init import init_db

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def post_init(application):
    await init_db()

def main():
    # إنشاء تطبيق البوت
    application = Application.builder().token(Config.TELEGRAM_TOKEN).post_init(post_init).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", user_handlers.start))
    
    # إضافة معالجات الأزرار
    application.add_handler(CallbackQueryHandler(user_handlers.show_investment_opportunities, pattern="^show_opportunities$"))
    
    # إضافة معالجات الأخطاء
    application.add_error_handler(error_handlers.error_handler)
    
    # بدء البوت
    application.run_polling()

if __name__ == "__main__":
    main()
