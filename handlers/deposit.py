from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from core.virtual_wallet import virtual_wallet
from utils.logger import user_logger

DEPOSIT_AMOUNT, DEPOSIT_CONFIRM = range(2)

async def start_deposit(update: Update, context: CallbackContext):
    """بدء عملية الإيداع"""
    user_id = str(update.effective_user.id)
    virtual_wallet.create_wallet(user_id)
    
    await update.message.reply_text(
        "💰 الرجاء إرسال مبلغ الإيداع (بالـUSDT):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء", callback_data="cancel_deposit")]
        ])
    )
    return DEPOSIT_AMOUNT

async def receive_deposit_amount(update: Update, context: CallbackContext):
    """استلام مبلغ الإيداع"""
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError
        
        context.user_data['deposit_amount'] = amount
        
        await update.message.reply_text(
            f"⚠️ الرجاء تحويل {amount} USDT إلى عنوان Binance التالي:\n\n"
            f"العنوان: {config.BINANCE_DEPOSIT_ADDRESS}\n"
            f"الشبكة: TRC20\n\n"
            "بعد الإيداع، أرسل hash المعاملة (Transaction Hash)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("إلغاء", callback_data="cancel_deposit")]
            ])
        )
        return DEPOSIT_CONFIRM
    except ValueError:
        await update.message.reply_text("⚠️ الرجاء إدخال مبلغ صحيح أكبر من الصفر")
        return DEPOSIT_AMOUNT

async def verify_transaction(update: Update, context: CallbackContext):
    """التحقق من صحة المعاملة"""
    user_id = str(update.effective_user.id)
    tx_hash = update.message.text.strip()
    
    await update.message.reply_text("🔍 جاري التحقق من المعاملة...")
    
    if await virtual_wallet.verify_deposit(user_id, tx_hash):
        balance = virtual_wallet.get_balance(user_id)
        await update.message.reply_text(
            f"✅ تم تأكيد الإيداع بنجاح!\n\n"
            f"الرصيد الحالي: {balance:.2f} USDT",
            reply_markup=main_menu_keyboard(user_id)
        )
    else:
        await update.message.reply_text(
            "❌ لم نتمكن من التحقق من الإيداع. الرجاء التأكد من:\n"
            "1. أن المعاملة تمت بنجاح\n"
            "2. أنك استخدمت الشبكة الصحيحة\n"
            "3. أن hash المعاملة صحيح",
            reply_markup=main_menu_keyboard(user_id)
        )
    
    return ConversationHandler.END
