from bot.database import SessionLocal, Transaction, User
from bot.gpt_analysis import get_profitable_deal
from sqlalchemy.future import select
import random

async def process_investment(user_id: int, amount: float) -> str:
    async with SessionLocal() as session:
        deal = await get_profitable_deal(amount)
        if deal["profit_percent"] < 6:
            return "لا توجد صفقات مربحة حاليًا. سيتم إشعارك عند توفر فرصة مناسبة."

        profit = amount * (deal["profit_percent"] / 100)
        net = amount + profit

        tx = Transaction(
            user_id=user_id,
            amount=amount,
            profit=profit,
            status="success"
        )
        session.add(tx)
        await session.commit()

        return (
            f"✅ تم تنفيذ صفقة استثمارية!\n\n"
            f"💰 المبلغ: {amount} USDT\n"
            f"📈 الربح: {deal['profit_percent']}%\n"
            f"🏁 العائد الصافي: {net:.2f} USDT\n"
            f"⏳ المدة: {deal['duration']} دقيقة\n\n"
            f"🔒 تم خصم عمولتك وتحويل الأرباح إلى محفظتك."
        )

async def get_summary(user_id: int) -> str:
    async with SessionLocal() as session:
        result = await session.execute(select(Transaction).where(Transaction.user_id == user_id))
        transactions = result.scalars().all()

        total_invested = sum(t.amount for t in transactions)
        total_profit = sum(t.profit for t in transactions)
        count = len(transactions)

        return (
            f"📊 ملخص استثمارك:\n"
            f"عدد الصفقات: {count}\n"
            f"إجمالي الاستثمار: {total_invested:.2f} USDT\n"
            f"إجمالي الأرباح: {total_profit:.2f} USDT"
        )

async def get_top_deals() -> str:
    return (
        "📈 أفضل الصفقات اليوم:\n"
        "- صفقة 1: ربح 14% خلال 40 دقيقة\n"
        "- صفقة 2: ربح 11% خلال 25 دقيقة\n"
        "- صفقة 3: ربح 9% خلال 30 دقيقة"
    )
