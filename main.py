# main.py
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from migrate_db import migrate
from handlers.start import start
from handlers.invest import handle_invest
from handlers.withdraw import handle_withdraw
from handlers.plans import handle_plan_selection, plan_callback
from handlers.admin import handle_admin_panel
from services.auto_invest import run_auto_invest
from config import BOT_TOKEN

# 🧱 تهيئة قاعدة البيانات تلقائيًا
migrate()

# 🚀 تشغيل الاستثمار التلقائي (يمكنك ربطه بـ scheduler لاحقًا)
run_auto_invest()

# 🧠 إعداد البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

# 🧭 أوامر المستخدم
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("invest", handle_invest))
app.add_handler(CommandHandler("withdraw", handle_withdraw))
app.add_handler(CommandHandler("plans", handle_plan_selection))
app.add_handler(CommandHandler("admin", handle_admin_panel))

# 📲 أزرار اختيار الخطة
app.add_handler(CallbackQueryHandler(plan_callback))

# ✅ تشغيل البوت
if __name__ == "__main__":
    print("✅ Bot is running...")
    app.run_polling()