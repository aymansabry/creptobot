from telegram import Update
from telegram.ext import CallbackContext
from core.virtual_wallet import get_virtual_wallet
from utils.logger import user_logger, log_error

virtual_wallet = get_virtual_wallet()

async def start(update: Update, context: CallbackContext):
    """بدء التفاعل مع البوت"""
    user_id = str(update.effective_user.id)
    try:
        virtual_wallet.create_wallet(user_id)
        await update.message.reply_text(
            f"مرحباً بك في نظام التداول الآلي\n"
            f"رصيدك الحالي: {virtual_wallet.get_balance(user_id):.2f} USDT\n\n"
            "استخدم الأوامر التالية:\n"
            "/deposit - لإيداع الأموال\n"
            "/trade - لبدء التداول\n"
            "/balance - لعرض رصيدك"
        )
    except Exception as e:
        log_error(f"Start command failed: {str(e)}", 'user')
        await update.message.reply_text("حدث خطأ في تهيئة المحفظة. الرجاء المحاولة لاحقاً.")

async def show_balance(update: Update, context: CallbackContext):
    """عرض رصيد المحفظة"""
    user_id = str(update.effective_user.id)
    try:
        balance = virtual_wallet.get_balance(user_id)
        await update.message.reply_text(f"رصيدك الحالي: {balance:.2f} USDT")
    except Exception as e:
        log_error(f"Balance check failed: {str(e)}", 'user')
        await update.message.reply_text("حدث خطأ في جلب الرصيد. الرجاء المحاولة لاحقاً.")
