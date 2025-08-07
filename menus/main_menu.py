from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Optional

async def show_main_menu(update, context: ContextTypes.DEFAULT_TYPE, message: Optional[str] = None):
    keyboard = [
        [InlineKeyboardButton("💰 فرص استثمارية", callback_data="show_opportunities")],
        [InlineKeyboardButton("💼 محفظتي", callback_data="show_wallet")],
        [InlineKeyboardButton("📊 سجل الصفقات", callback_data="trade_history")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")]
    ]
    
    text = message or """🏦 مرحباً بك في نظام التداول الآلي بالمراجحة

📊 اختر أحد الخيارات التالية للبدء:"""
    
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        from utils.logger import logger
        logger.error(f"Error in show_main_menu: {str(e)}")
        if update.message:
            await update.message.reply_text("حدث خطأ في عرض القائمة الرئيسية")
