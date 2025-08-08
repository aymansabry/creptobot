# project_root/handlers/user.py

import re
from telegram import Update
from telegram.ext import ContextTypes
from db import crud
from db.database import async_session
from ui.menus import trading_options_menu, user_main_menu
from services.trade_logic import TradeLogic
from services.trade_executor import TradeExecutor
from services.wallet_manager import WalletManager
from utils.constants import MESSAGES
import asyncio

# Initialize services
trade_executor = TradeExecutor()
wallet_manager = WalletManager()

trade_logic = None

async def handle_start_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global trade_logic
    if not trade_logic:
        trade_logic = TradeLogic(context.bot)

    available_trades_info = """
    **صفقات متاحة حالياً:**
    1. BTC/USDT (ربح محتمل 3%)
    2. ETH/USDT (ربح محتمل 5%)
    3. SOL/USDT (ربح محتمل 7%)
    4. ADA/USDT (ربح محتمل 4%)
    5. XRP/USDT (ربح محتمل 6%)
    """
    
    await update.message.reply_markdown(available_trades_info)
    await update.message.reply_text(
        MESSAGES['trading_options'],
        reply_markup=trading_options_menu
    )

async def handle_auto_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with async_session() as db_session:
        wallet = await crud.get_wallet_by_user_id(db_session, user_id)
        
        if not wallet:
            await update.message.reply_text("عذراً، لم يتم العثور على محفظتك. يرجى إعادة تشغيل البوت.")
            return

        if wallet.is_continuous_trading:
            # Stop continuous trading
            trade_logic.stop_continuous_trading(user_id)
            wallet.is_continuous_trading = False
            await db_session.commit()
            await update.message.reply_text(MESSAGES['continuous_trading_deactivated'], reply_markup=user_main_menu)
            
        else:
            # Start continuous trading
            if wallet.balance_usdt < 1.0:
                await update.message.reply_text(MESSAGES['insufficient_balance'])
                return
            
            wallet.is_continuous_trading = True
            await db_session.commit()
            
            asyncio.create_task(trade_logic.continuous_trading_loop(user_id))
            await update.message.reply_text(MESSAGES['continuous_trading_activated'])
            

async def handle_manual_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    result = await trade_logic.execute_single_trade(user_id)
    if result == "insufficient_balance":
        await update.message.reply_text(MESSAGES['insufficient_balance'])
    elif result == "success":
        await update.message.reply_text("تم إرسال طلب صفقة واحدة. ستصلك التفاصيل قريباً.")

async def handle_view_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with async_session() as db_session:
        wallet = await crud.get_wallet_by_user_id(db_session, user_id)
        balance = wallet.balance_usdt if wallet else 0.0
        message = f"رصيدك الحالي هو: **{balance:.2f} USDT**"
        await update.message.reply_markdown(message)

async def handle_deposit_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """
    **لإيداع مبلغ:**
    أرسل لنا رسالة تحتوي على:
    `إيداع [المبلغ]`
    مثال: `إيداع 100`
    
    **للسحب:**
    أرسل لنا رسالة تحتوي على:
    `سحب [المبلغ]`
    مثال: `سحب 50`
    
    سيتم مراجعة طلبك من قبل المدير.
    """
    await update.message.reply_markdown(message)
    
async def handle_deposit_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    
    match = re.match(r"إيداع\s+(\d+(\.\d+)?)", message_text)
    if match:
        amount = float(match.group(1))
        
        async with async_session() as db_session:
            # For now, we'll auto-approve and add the funds
            await crud.update_wallet_balance(db_session, user_id, amount)
            await crud.create_transaction(db_session, user_id, "deposit", amount)
            await update.message.reply_text(f"✅ تم تأكيد إيداع مبلغ {amount:.2f} USDT. تم تحديث رصيدك.")

async def handle_withdraw_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    
    match = re.match(r"سحب\s+(\d+(\.\d+)?)", message_text)
    if match:
        amount = float(match.group(1))
        async with async_session() as db_session:
            wallet = await crud.get_wallet_by_user_id(db_session, user_id)
            if not wallet or wallet.balance_usdt < amount:
                await update.message.reply_text("عذراً، رصيدك لا يكفي لإتمام عملية السحب.")
                return

            await crud.update_wallet_balance(db_session, user_id, -amount)
            await crud.create_transaction(db_session, user_id, "withdrawal", amount)
            await update.message.reply_text(f"✅ تم تأكيد سحب مبلغ {amount:.2f} USDT. سيتم تحويله قريباً.")
