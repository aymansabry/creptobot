# services/auto_invest.py
from database.connection import get_connection
from services.profit_calculator import calculate_profit

def run_auto_invest():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        balance = user[4]
        plan = user[3]

        # توزيع الأرباح حسب الخطة
        from utils.helpers import get_plan_distribution
        dist = get_plan_distribution(plan)

        total_profit = 0
        for t, ratio in dist.items():
            profit = calculate_profit(balance * ratio, t)
            total_profit += profit
            cursor.execute("INSERT INTO profits (user_id, amount, type) VALUES (?, ?, ?)", (user_id, profit, t))

        # خصم نسبة البوت
        cursor.execute("SELECT bot_share_percent FROM admin_settings WHERE id = 1")
        bot_percent = cursor.fetchone()[0]
        bot_share = total_profit * (bot_percent / 100)
        net_profit = total_profit - bot_share

        # تحديث الرصيد
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (net_profit, user_id))

    conn.commit()
    conn.close()