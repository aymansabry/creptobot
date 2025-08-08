# project_root/handlers/user.py

from telegram import Update
from telegram.ext import ContextTypes
from db import crud
from db.database import async_session
from ui.menus import trading_options_menu
from services.trade_logic import TradeLogic
from services.trade_executor import TradeExecutor
from services.wallet_manager import WalletManager
from utils.constants import MESSAGES
import asyncio

# Initialize services
trade_executor = TradeExecutor()
wallet_manager = WalletManager()

# This part needs to be initialized with the bot instance
trade_logic = None

async def handle_start_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'بدء التداول' button."""
    global trade_logic
    if not trade_logic:
        trade_logic = TradeLogic(context.bot)

    await update.message.reply_text(
        MESSAGES['trading_options'],
        reply_markup=trading_options_menu
    )

async def handle_auto_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'تفعيل التداول المستمر' button."""
    user_id = update.effective_user.id
    async with async_session() as db_session:
        wallet = await crud.get_wallet_by_user_id(db_session, user_id)
        if not wallet or wallet.balance_usdt < 1.0:
            await update.message.reply_text(MESSAGES['insufficient_balance'])
            return
            
        wallet.is_continuous_trading = True
        await db_session.commit()
        await update.message.reply_text(MESSAGES['continuous_trading_activated'])
    
    asyncio.create_task(trade_logic.continuous_trading_loop(user_id))
    
async def handle_manual_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'صفقة واحدة' button."""
    user_id = update.effective_user.id
    result = await trade_logic.execute_single_trade(user_id)
    if result == "insufficient_balance":
        await update.message.reply_text(MESSAGES['insufficient_balance'])
    elif result == "success":
        await update.message.reply_text("تم إرسال طلب صفقة واحدة. ستصلك التفاصيل قريباً.")

async def handle_view_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'عرض الرصيد' button."""
    user_id = update.effective_user.id
    async with async_session() as db_session:
        wallet = await crud.get_wallet_by_user_id(db_session, user_id)
        balance = wallet.balance_usdt if wallet else 0.0
        message = f"رصيدك الحالي هو: **{balance:.2f} USDT**"
        await update.message.reply_markdown(message)
