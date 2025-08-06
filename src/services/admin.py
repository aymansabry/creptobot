from src.database.models import get_total_investment_stats, set_profit_percentage, get_profit_percentage

async def get_dashboard_data() -> str:
    stats = await get_total_investment_stats()
    percentage = await get_profit_percentage()
    return (
        f"👥 العملاء: {stats['total_users']}\n"
        f"💼 إجمالي المستثمرين: {stats['investors']}\n"
        f"💰 الأرباح الكلية: {stats['total_profits']:.2f} USDT\n"
        f"📊 نسبة ربح البوت: {percentage}%"
    )

async def set_bot_profit_percentage(p: float):
    await set_profit_percentage(p)

async def get_bot_profit_percentage() -> float:
    return await get_profit_percentage()
