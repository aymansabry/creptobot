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
    
    text = message or "🏦 مرحباً بك في نظام التداول الآلي بالمراجحة\n\n" \
                     "📊 اختر أحد الخيارات التالية للبدء:"
    
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

async def show_wallet_menu(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    wallet = await context.bot_data['db_session'].execute(
        f"SELECT balances FROM wallets WHERE user_id = {user.id} LIMIT 1"
    )
    balances = wallet.scalar() if wallet else {'USDT': 0.0}
    
    balance_text = "\n".join([f"• {currency}: {amount:.2f}" for currency, amount in balances.items()])
    
    keyboard = [
        [InlineKeyboardButton("➕ إيداع", callback_data="deposit")],
        [InlineKeyboardButton("➖ سحب", callback_data="withdraw")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    
    await update.callback_query.edit_message_text(
        f"💼 محفظتك الافتراضية:\n\n{balance_text}\n\n"
        "اختر الإجراء المطلوب:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_trade_history(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    trades = await context.bot_data['db_session'].execute(
        f"SELECT * FROM trades WHERE user_id = {user.id} ORDER BY created_at DESC LIMIT 5"
    )
    trades = trades.fetchall()
    
    if not trades:
        history_text = "📭 لا توجد صفقات مسجلة حتى الآن."
    else:
        history_text = "📊 آخر 5 صفقات:\n\n"
        for trade in trades:
            history_text += (
                f"🆔 {trade.id}\n"
                f"📊 {trade.symbol}\n"
                f"💰 الربح: {trade.profit:.2f} USDT\n"
                f"📅 {trade.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"————————————\n"
            )
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    
    await update.callback_query.edit_message_text(
        history_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_settings_menu(update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔔 إعدادات الإشعارات", callback_data="notification_settings")],
        [InlineKeyboardButton("💱 العملة المفضلة", callback_data="currency_settings")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    
    await update.callback_query.edit_message_text(
        "⚙️ إعدادات حسابك:\n\n"
        "اختر الإعداد الذي ترغب في تعديله:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
