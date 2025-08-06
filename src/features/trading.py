from decimal import Decimal
from src.utils.arbitrage_engine import find_profitable_opportunity, execute_trade
from src.database.models_helpers import get_user_by_telegram_id, update_user_wallet_balance, log_transaction
from src.utils.notifications import notify_user
from src.utils.constants import BOT_FEE_PERCENTAGE

async def process_single_investment(bot, telegram_id: int, amount: Decimal, min_profit: float):
    user = await get_user_by_telegram_id(telegram_id)
    if not user or user.wallet_balance < amount:
        await notify_user(bot, telegram_id, "❌ رصيدك لا يكفي لإتمام الاستثمار.")
        return False

    opportunity = find_profitable_opportunity(min_profit)
    if not opportunity:
        await notify_user(bot, telegram_id, "⚠️ لم يتم العثور على صفقة مربحة حاليًا، جاري انتظار الفرصة المناسبة.")
        return False

    net_profit = execute_trade(amount, opportunity["profit_percent"])
    bot_fee = (net_profit * BOT_FEE_PERCENTAGE) / 100
    client_earning = net_profit - bot_fee

    await update_user_wallet_balance(telegram_id, client_earning)
    await log_transaction(telegram_id, amount, client_earning, bot_fee, "completed")

    await notify_user(bot, telegram_id, (
        f"✅ تم تنفيذ صفقة:\n"
        f"🔄 شراء من: {opportunity['buy_from']} | بيع إلى: {opportunity['sell_to']}\n"
        f"📈 ربح الصفقة: {opportunity['profit_percent']}٪\n"
        f"💰 ربحك: {client_earning:.4f} USDT\n"
        f"🤖 عمولة البوت: {bot_fee:.4f} USDT"
    ))

    # يمكن لاحقًا هنا إرسال العمولة لمحفظة المدير فعليًا عبر TRON API
    return True
