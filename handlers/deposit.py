from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from core.virtual_wallet import get_virtual_wallet
from utils.logger import user_logger, log_error
from core.config import config

virtual_wallet = get_virtual_wallet()

DEPOSIT_AMOUNT, DEPOSIT_CONFIRM = range(2)

async def start_deposit(update: Update, context: CallbackContext):
    """بدء عملية الإيداع"""
    user_id = str(update.effective_user.id)
    try:
        virtual_wallet.create_wallet(user_id)
        user_logger.info(f"Deposit started for user {user_id}")
        
        await update.message.reply_text(
            "💰 الرجاء إرسال مبلغ الإيداع (بالـUSDT):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("إلغاء", callback_data="cancel_deposit")]
            ])
        )
        return DEPOSIT_AMOUNT
    except Exception as e:
        log_error(f"Deposit start failed: {str(e)}", 'user')
        await update.message.reply_text("حدث خطأ في بدء عملية الإيداع. الرجاء المحاولة لاحقاً.")
        return ConversationHandler.END

# ... باقي دوال الإيداع بنفس النمط ...
