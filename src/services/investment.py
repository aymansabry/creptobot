from aiogram import types
from src.database.models import (
    get_user_wallet, update_user_wallet_balance,
    save_investment_transaction, get_bot_profit_percentage
)
from src.services.ai import suggest_deals
from decimal import Decimal

async def handle_auto_invest(msg: types.Message):
    wallet = await get_user_wallet(msg.from_user.id)
    if not wallet or wallet.balance <= 0:
        return await msg.answer("رصيدك غير كافٍ للاستثمار.")

    deals_text = await suggest_deals()
    if "لا توجد صفقات" in deals_text:
        return await msg.answer("لا توجد صفقات مربحة حالياً. سيتم استثمارك عند توفر صفقات جديدة تلقائياً.")

    amount = wallet.balance
    profit_percentage = await get_bot_profit_percentage()

    gross_profit = amount * Decimal("0.04")  # مثال ربح 4%
    bot_fee = gross_profit * profit_percentage / Decimal("100")
    net_profit = gross_profit - bot_fee

    new_balance = amount + net_profit
    await update_user_wallet_balance(msg.from_user.id, new_balance)
    await save_investment_transaction(msg.from_user.id, amount, net_profit, bot_fee)

    await msg.answer(
        f"✅ تم تنفيذ صفقة ناجحة!\n\n💵 المبلغ المستثمر: {amount} USDT\n"
        f"💰 الربح الصافي: {net_profit:.2f} USDT\n"
        f"🏦 الرصيد الجديد: {new_balance:.2f} USDT"
    )
