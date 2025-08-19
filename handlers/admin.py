# handlers/admin.py
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import get_connection

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != 123456789:  # غير الرقم ده لـ Telegram ID بتاعك
        await update.message.reply_text("غير مصرح لك بالدخول للوحة التحكم ❌")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT bot_share_percent, wallet_address FROM admin_settings WHERE id = 1")
    settings = cursor.fetchone()
    conn.close()

    await update.message.reply_text(
        f"🔧 إعدادات البوت:\n\nنسبة البوت: {settings[0]}%\nعنوان المحفظة: {settings[1] or 'غير محدد'}"
    )