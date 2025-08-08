# project_root/handlers/common.py

from telegram import Update
from telegram.ext import ContextTypes
from db import crud
from db.database import async_session
from ui.menus import user_main_menu, admin_main_menu
from core.config import settings

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    async with async_session() as db_session:
        user = await crud.get_user(db_session, user_id)
        if not user:
            user = await crud.create_user(db_session, user_id, username)
            await crud.create_wallet(db_session, user.user_id)
        
        if user_id == settings.ADMIN_ID:
            await update.message.reply_text("👋 أهلًا بك يا مدير! هذه لوحة تحكم الإدارة.", reply_markup=admin_main_menu)
        else:
            await update.message.reply_text("👋 أهلًا بك في بوت التداول الآلي!", reply_markup=user_main_menu)
