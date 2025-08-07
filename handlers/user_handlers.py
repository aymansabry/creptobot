from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from typing import Dict, Any
from db.crud import get_user, create_user, get_user_wallet, create_wallet
from db.models import User
from utils.logger import logger
from notifications.telegram_notifier import send_notification
from menus.main_menu import show_main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        db_session = context.bot_data['db_session']
        db_user = await get_user(db_session, user.id)
        
        if not db_user:
            new_user = {
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            db_user = await create_user(db_session, new_user)
            
            wallet_data = {
                'user_id': db_user.id,
                'address': f"user_{user.id}_wallet",
                'balances': {'USDT': 0.0}
            }
            await create_wallet(db_session, wallet_data)
            
            await send_notification(
                context.bot,
                context.bot_data['admin_ids'][0],
                f"👤 مستخدم جديد: {user.full_name} (ID: {user.id})"
            )
        
        await show_main_menu(update, context, "🎉 مرحباً بك! اختر الخيار المناسب:")
        
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء بدء التشغيل، يرجى المحاولة لاحقاً")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

def setup_user_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
