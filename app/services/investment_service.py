from app.utils.ai_strategy import get_best_trade
from app.utils.tron_utils import send_trx
from app.database.models import Investment, User
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

BOT_PROFIT_PERCENTAGE = 0.05  # 5%

async def process_investment(user: User, amount: float, session: AsyncSession):
    # تنفيذ صفقة ذكية (وهمية أو واقعية)
    profit = amount * 0.1  # مثال: ربح 10%
    total = amount + profit

    # حساب العمولة وتحويلها لمحفظة TRON الخاصة بالمالك
    bot_cut = total * BOT_PROFIT_PERCENTAGE
    send_trx(user.owner_wallet, bot_cut)

    # تسجيل الاستثمار
    investment = Investment(
        user_id=user.id,
        amount=amount,
        profit=profit,
        net_amount=total - bot_cut,
        timestamp=datetime.utcnow()
    )
    session.add(investment)
    await session.commit()
    return investment
