import os
from telegram.ext import Application
from handlers.user_handler import start_handler, handle_user_selection, text_handler

BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة الـ handlers
    application.add_handler(start_handler)
    application.add_handler(handle_user_selection)
    application.add_handler(text_handler)

    # تشغيل البوت بنظام Polling
    application.run_polling()

if __name__ == "__main__":
    main()
