import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from handlers import set_amount, virtual_invest, real_invest
from database import init_db
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعداد اللوجات
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# رسالة بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت الاستثمار\n"
        "💰 ابدأ بتحديد المبلغ باستخدام:\n"
        "/set_amount 100\n\n"
        "ثم اختر الاستثمار الوهمي أو الحقيقي من القائمة."
    )

# ربط أزرار الكولباك
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "virtual_invest":
        await virtual_invest(update, context)
    elif data == "real_invest":
        await real_invest(update, context)
    else:
        await query.answer("❌ أمر غير معروف")

# دالة تشغيل البوت
def main():
    # إنشاء قاعدة البيانات إذا لم تكن موجودة
    init_db()

    # تشغيل التطبيق
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_amount", set_amount))

    # الكولباك
    app.add_handler(CallbackQueryHandler(callback_router))

    # تشغيل البوت
    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
