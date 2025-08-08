# project_root/handlers/common.py

from telegram import Update
from telegram.ext import ContextTypes
from db import crud
from db.database import async_session
from ui.menus import user_main_menu, admin_main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    async with async_session() as db_session:
        user = await crud.get_user_by_telegram_id(db_session, user_id)
        if not user:
            user = await crud.create_user(db_session, user_id, username)
            message = "أهلاً بك! لقد تم إنشاء حسابك بنجاح. يمكنك الآن بدء التداول."
        else:
            message = "أهلاً بعودتك! اختر أحد الخيارات من القائمة الرئيسية."

    if user and user.is_admin:
        await update.message.reply_text(message, reply_markup=admin_main_menu)
    else:
        await update.message.reply_text(message, reply_markup=user_main_menu)
