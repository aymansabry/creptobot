# project_root/handlers/admin.py

from telegram import Update
from telegram.ext import ContextTypes
from db.database import async_session
from db import crud
from core.config import settings
from db.models import User
from sqlalchemy.future import select

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /admin command and checks for admin permissions."""
    if update.effective_user.id != settings.ADMIN_ID:
        await update.message.reply_text("عفواً، لا تملك صلاحيات الوصول إلى لوحة الإدارة.")
        return
    
    await update.message.reply_text("أهلاً بك أيها المدير! اختر أحد الخيارات من لوحة التحكم.")

async def handle_view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays a list of all registered users."""
    if update.effective_user.id != settings.ADMIN_ID:
        return

    async with async_session() as db_session:
        users = await db_session.execute(select(User))
        user_list = users.scalars().all()
        
        message = "قائمة المستخدمين:\n"
        for user in user_list:
            message += f"- ID: `{user.telegram_id}` | Username: `{user.username}` | Admin: `{user.is_admin}`\n"
        
        await update.message.reply_markdown(message)
