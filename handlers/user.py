# project_root/handlers/user.py

import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db import crud
from db.database import async_session
from ui.menus import trading_options_menu, user_main_menu, trade_type_menu
from services.trade_logic import TradeLogic
from services.trade_executor import TradeExecutor
from services.wallet_manager import WalletManager
from utils.constants import MESSAGES
import asyncio
from core.config import settings

# Initialize services
trade_executor = TradeExecutor()
wallet_manager = WalletManager()

trade_logic = None

async def handle_start_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'ابدأ التداول' button, showing trade type options."""
    global trade_logic
    if not trade_logic:
        trade_logic = TradeLogic(context.bot)

    await update.message.reply_text(
        "اختر نوع الصفقة التي ترغب بها:",
        reply_markup=trade_type_menu
    )
    
async def handle_trial_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for starting a trial trade."""
    await update.message.reply_text("هذه صفقة تجريبية. سيتم محاكاة التداول بدون أي أموال حقيقية.")
    # TODO: Implement the trial trading logic here
    
async def handle_real_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays real AI-generated trades to the user.
    """
    global trade_logic
    if not trade_logic:
        trade_logic = TradeLogic(context.bot)

    trades = await trade_logic.get_ai_trades()
    
    if not trades:
        await update.message.reply_text("عذراً، لم أتمكن من توليد صفقات في الوقت الحالي. يرجى المحاولة لاحقاً.")
        return

    available_trades_info = "**صفقات متاحة حالياً (مقترحة بواسطة AI):**\n"
    for i, trade in enumerate(trades):
        profit_factor = trade['potential_profit'] / 100
        net_profit_rate = (profit_factor - (profit_factor * trade['commission_rate']) - trade['exchange_fees']) * 100
        
        available_trades_info += (
            f"{i+1}. **{trade['symbol']}** (كود: `{trade['code']}`)\n"
            f"   - منصة التداول: {trade['exchange'].upper()}\n"
            f"   - الربح المتوقع: **{trade['potential_profit']:.2f}%**\n"
            f"   - صافي الربح بعد الرسوم والعمولة: **{net_profit_rate:.2f}%**\n"
            f"   - مدة التنفيذ القصوى: **{trade['duration_minutes']} دقيقة**\n"
            f"   - استراتيجية الدخول: {trade['entry_strategy']}\n"
            f"   - استراتيجية الخروج: {trade['exit_strategy']}\n\n"
        )
        
    await update.message.reply_markdown(available_trades_info)
    await update.message.reply_text(
        "اختر نوع الصفقة التي ترغب بها:",
        reply_markup=trading_options_menu
    )
    
async def handle_auto_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles continuous trading on or off."""
    user_id = update.effective_user.id
    async with async_session() as db_session:
        wallet = await crud.get_wallet_by_user_id(db_session, user_id)
        
        if not wallet:
            await update.message.reply_text("عذراً، لم يتم العثور على محفظتك. يرجى إعادة تشغيل البوت.")
            return

        if wallet.is_continuous_trading:
            trade_logic.stop_continuous_trading(user_id)
            wallet.is_continuous_trading = False
            await db_session.commit()
            await update.message.reply_text(MESSAGES['continuous_trading_deactivated'], reply_markup=user_main_menu)
        else:
            if wallet.balance_usdt < 1.0:
                await update.message.reply_text(MESSAGES['insufficient_balance'])
                return
            
            wallet.is_continuous_trading = True
            await db_session.commit()
            
            asyncio.create_task(trade_logic.continuous_trading_loop(user_id))
            await update.message.reply_text(MESSAGES['continuous_trading_activated'])
            
async def handle_manual_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'صفقة واحدة' button."""
    user_id = update.effective_user.id
    
    recommendations = await trade_logic.get_ai_trades()
    if not recommendations:
        await update.message.reply_text("عذراً، لم أتمكن من توليد صفقة في الوقت الحالي. يرجى المحاولة لاحقاً.")
        return
        
    await trade_logic.execute_single_trade(user_id, recommendations[0])
    
async def handle_view_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'عرض الرصيد' button."""
    user_id = update.effective_user.id
    async with async_session() as db_session:
        wallet = await crud.get_wallet_by_user_id(db_session, user_id)
        balance = wallet.balance_usdt if wallet else 0.0
        message = f"رصيدك الحالي هو: **{balance:.2f} USDT**"
        await update.message.reply_markdown(message)

async def handle_deposit_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guides the user on how to deposit or withdraw funds."""
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
    """Initiates the automated deposit process."""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    match = re.match(r"إيداع\s+(\d+(\.\d+)?)", message_text)
    if match:
        amount = float(match.group(1))
        
        if 'deposit_amount' in context.user_data:
            await update.message.reply_text("هناك عملية إيداع قيد التنفيذ بالفعل. يرجى إكمالها أولاً.")
            return

        deposit_address = await wallet_manager.get_deposit_address(user_id)
        
        context.user_data['deposit_amount'] = amount
        context.user_data['deposit_address'] = deposit_address
        
        message = f"""
        **لإتمام عملية الإيداع:**
        يرجى إرسال مبلغ **{amount:.2f} USDT** إلى العنوان التالي:
        
        `{deposit_address}`
        
        **ملاحظة:** تأكد من أن الشبكة المستخدمة هي **TRC20**.
        
        بعد إتمام عملية الإيداع، يرجى الضغط على الزر التالي لتأكيد العملية.
        """
        await update.message.reply_markdown(message, reply_markup=ReplyKeyboardMarkup([["تم الإيداع"]], resize_keyboard=True, one_time_keyboard=True))
        
async def handle_deposit_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'تم الإيداع' button and starts the automated verification."""
    user_id = update.effective_user.id
    amount = context.user_data.get('deposit_amount')
    deposit_address = context.user_data.get('deposit_address')
    
    if not amount or not deposit_address:
        await update.message.reply_text("عذراً، يبدو أن هناك خطأ. يرجى إعادة إرسال طلب الإيداع.", reply_markup=user_main_menu)
        return

    await update.message.reply_text("جاري التحقق من عملية الإيداع. قد تستغرق هذه العملية بضع دقائق.", reply_markup=user_main_menu)

    is_confirmed = await wallet_manager.check_deposit_status(user_id, amount)
    
    if is_confirmed:
        async with async_session() as db_session:
            await crud.update_wallet_balance(db_session, user_id, amount)
            await crud.create_transaction(db_session, user_id, "deposit", amount)
        
        await update.message.reply_text(f"✅ تم تأكيد إيداع مبلغ {amount:.2f} USDT. تم تحديث رصيدك تلقائياً!")
    else:
        await update.message.reply_text("عذراً، لم يتم العثور على الإيداع. يرجى المحاولة مرة أخرى أو التواصل مع الدعم.")
        
    context.user_data.pop('deposit_amount', None)
    context.user_data.pop('deposit_address', None)

async def handle_withdraw_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles withdraw requests from users."""
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

            success = await wallet_manager.process_withdrawal(user_id, amount, "USER_WITHDRAWAL_ADDRESS")
            
            if success:
                await crud.update_wallet_balance(db_session, user_id, -amount)
                await crud.create_transaction(db_session, user_id, "withdrawal", amount)
                await update.message.reply_text(f"✅ تم تأكيد سحب مبلغ {amount:.2f} USDT. سيتم تحويله تلقائياً إلى محفظتك.")
            else:
                await update.message.reply_text("عذراً، حدث خطأ أثناء معالجة السحب. يرجى المحاولة مرة أخرى.")
