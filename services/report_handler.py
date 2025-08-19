from aiogram import types
from services.report import generate_report

async def show_user_report(msg: types.Message):
    report = generate_report(msg.from_user.id)
    text = f"""
📊 كشف حسابك:
- عدد الصفقات: {report['trade_count']}
- إجمالي الأرباح: {report['total_profit']} $
- نسبة البوت: {report['bot_share']} $
- صافي الربح: {report['net_user_profit']} $
- الرصيد الحالي: {report['balance']} $

🕒 آخر صفقة:
{report['last_trade']['path']} | ربح: {report['last_trade']['profit']} $
في: {report['last_trade']['timestamp']}
""" if report["last_trade"] else "لا توجد صفقات حتى الآن."

    await msg.answer(text)