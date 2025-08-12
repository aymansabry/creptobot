#main.py
import os
import subprocess
import logging
import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram import Update
from database import SessionLocal
from models import User
from handlers import (
    start as handlers_start,
    handle_menu_choice,
    add_platform_receive_exchange_name,
    add_platform_receive_api_key,
    add_platform_receive_api_secret,
    receive_investment_amount,
    handle_investment_type,
    cancel,
    get_end_date,
)
from handlers import (
    CHOOSE_MENU,
    ENTER_API_KEY,
    ENTER_API_SECRET,
    CHOOSE_PLATFORM,
    ENTER_INVESTMENT_AMOUNT,
    CHOOSE_INVESTMENT_TYPE,
    ENTER_START_DATE,
    ENTER_END_DATE,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود! تأكد من وضعه في متغيرات البيئة.")


def run_migrations():
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("✅ المايجريشن تم بنجاح.")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل المايجريشن: {e}")


def delete_webhook():
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        resp = requests.post(url)
        if resp.status_code == 200:
            logger.info("✅ تم حذف Webhook القديم بنجاح.")
        else:
            logger.warning(f"⚠️ فشل حذف Webhook: {resp.text}")
    except Exception as e:
        logger.error(f"❌ خطأ أثناء حذف Webhook: {e}")


def register_user(user_id):
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.telegram_id == user_id).first()
        if not existing_user:
            new_user = User(telegram_id=user_id, role="client")
            db.add(new_user)
            db.commit()
            logger.info(f"✅ تم تسجيل مستخدم جديد: {user_id}")
    except Exception as e:
        logger.error(f"❌ خطأ أثناء تسجيل المستخدم: {e}")
    finally:
        db.close()


# نستخدم نسخة من دالة start اللي في handlers.py لكن مع تسجيل المستخدم
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    return await handlers_start(update, context)


def main():
    run_migrations()
    delete_webhook()

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MENU: [CommandHandler("start", start),  # ممكن تعيد /start داخل القائمة
                          filters.CallbackQueryHandler(handle_menu_choice)],
            ENTER_API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_platform_receive_exchange_name)],
            ENTER_API_SECRET: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_platform_receive_api_key)],
            CHOOSE_PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_platform_receive_api_secret)],
            ENTER_INVESTMENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_investment_amount)],
            CHOOSE_INVESTMENT_TYPE: [filters.CallbackQueryHandler(handle_investment_type)],
            ENTER_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: c.user_data.update({'start_date': u.message.text}) or get_end_date(u,c))],
            ENTER_END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)],  # عدلها حسب الخطوات اللي عندك
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    logger.info("🚀 البوت بدأ ويعمل في وضع polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
