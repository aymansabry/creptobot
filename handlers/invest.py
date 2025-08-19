# handlers/invest.py
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import get_connection
from database.models import get_user_by_telegram_id
from utils.logger import log_action

async def handle_invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if not args or not args[0].isdigit():
        await update.message.reply_text("اكتب المبلغ اللي عايز تستثمره بعد الأمر، زي: /invest 100")
        return

    amount = float(args[0])
    user_data = get_user_by_telegram_id(user.id)

    if not user_data:
        await update.message.reply_text("سجل أولًا باستخدام /start")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO investments (user_id, amount, type) VALUES (?, ?, ?)", (user_data[0], amount, "manual"))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_data[0]))
    conn.commit()
    conn.close()

    log_action(user_data[0], "invest", f"Invested {amount}")
    await update.message.reply_text(f"تم استثمار {amount} بنجاح ✅")