from telegram import Update
from telegram.ext import CallbackContext
from core.trading_engine import TradingEngine
from core.virtual_wallet import get_virtual_wallet
from utils.logger import trade_logger, log_error

engine = TradingEngine()
virtual_wallet = get_virtual_wallet()

async def start_trading(update: Update, context: CallbackContext):
    """بدء عملية التداول"""
    user_id = str(update.effective_user.id)
    try:
        balance = virtual_wallet.get_balance(user_id)
        await update.message.reply_text(
            f"💰 رصيدك المتاح: {balance:.2f} USDT\n"
            "أرسل زوج التداول والمبلغ (مثال: BTCUSDT 10)"
        )
    except Exception as e:
        log_error(f"Trade start failed: {str(e)}", 'trade')
        await update.message.reply_text("حدث خطأ في بدء التداول. الرجاء المحاولة لاحقاً.")

async def execute_trade(update: Update, context: CallbackContext):
    """تنفيذ صفقة"""
    user_id = str(update.effective_user.id)
    try:
        text = update.message.text.split()
        pair = text[0].upper()
        amount = float(text[1])
        
        result = await engine.execute_trade(user_id, pair, amount)
        
        if result['status'] == 'completed':
            await update.message.reply_text(
                f"✅ تم تنفيذ الصفقة بنجاح!\n"
                f"الربح: {result['profit']:.2f} USDT\n"
                f"الرصيد الجديد: {virtual_wallet.get_balance(user_id):.2f} USDT"
            )
        else:
            await update.message.reply_text(f"❌ فشل التداول: {result['error']}")
            
    except Exception as e:
        log_error(f"Trade execution failed: {str(e)}", 'trade')
        await update.message.reply_text("حدث خطأ أثناء التداول. الرجاء التحقق من المدخلات والمحاولة مرة أخرى.")
