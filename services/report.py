from database.init_db import SessionLocal
from database.models import User, ArbitrageLog
from datetime import datetime

session = SessionLocal()

def generate_daily_report(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    logs = session.query(ArbitrageLog).filter_by(user_id=user.id).all()

    total_profit = sum([log.profit for log in logs])
    last_trade = logs[-1] if logs else None

    report = f"""
📊 تقريرك اليومي:
- عدد الصفقات: {len(logs)}
- إجمالي الأرباح: ${round(total_profit, 2)}
- الرصيد الحالي: ${round(user.balance, 2)}
"""

    if last_trade:
        report += f"""
🕒 آخر صفقة:
- الزوج: {last_trade.symbol}
- الكمية: {last_trade.amount}
- الربح: ${round(last_trade.profit, 2)}
- في: {last_trade.executed_at.strftime('%Y-%m-%d %H:%M')}
"""

    return report
