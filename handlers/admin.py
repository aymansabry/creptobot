# project_root/handlers/admin.py

from telegram import Update
from telegram.ext import ContextTypes
from ui.menus import admin_main_menu, user_main_menu
from core.config import settings

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the admin panel menu."""
    if update.effective_user.id != settings.ADMIN_ID:
        return
    await update.message.reply_text("أهلاً بك في لوحة تحكم الإدارة.", reply_markup=admin_main_menu)

async def handle_view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for viewing users."""
    if update.effective_user.id != settings.ADMIN_ID:
        return
    await update.message.reply_text("جاري عرض قائمة المستخدمين...")
    # TODO: Implement database query to fetch and display users

async def handle_switch_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows the admin to switch to the regular user menu."""
    if update.effective_user.id != settings.ADMIN_ID:
        return
    await update.message.reply_text("تم التبديل إلى وضع المستخدم العادي.", reply_markup=user_main_menu)

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provides instructions for how to modify settings."""
    if update.effective_user.id != settings.ADMIN_ID:
        return
    await update.message.reply_text("لإجراء تعديل على الإعدادات، يرجى إرسال الأمر بالصيغة التالية:\n\n`تغيير [اسم الإعداد] [القيمة الجديدة]`\n\nمثال: `تغيير عمولة_البوت 0.05`", reply_markup=admin_main_menu)
