# handlers.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import query_one, execute, query
from utils import send_notification_to_user, send_admin_alert

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    existing = query_one("SELECT * FROM users WHERE telegram_id=%s", (tg.id,))
    if not existing:
        execute("INSERT INTO users (telegram_id, username) VALUES (%s,%s)", (tg.id, tg.username or tg.first_name))
        # notify admins
        send_admin_alert("مستخدم جديد", f"User @{tg.username or tg.first_name} ({tg.id}) سجل في البوت.")
    kb = [
        [InlineKeyboardButton("📈 بدء الاستثمار", callback_data="invest")],
        [InlineKeyboardButton("⚙️ إعدادات API", callback_data="api_settings")],
        [InlineKeyboardButton("📊 تقارير", callback_data="reports")],
    ]
    await update.message.reply_text("أهلاً! اختر من القائمة:", reply_markup=InlineKeyboardMarkup(kb))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    data = cq.data
    tg = cq.from_user
    if data == "invest":
        user = query_one("SELECT * FROM users WHERE telegram_id=%s", (tg.id,))
        await cq.edit_message_text(f"رصيدك الحالي: {user.get('invested_amount',0)}\nلاختيار وضع تجريبي / حقيقي استخدم الأوامر.")
    elif data == "api_settings":
        text = ("لإضافة مفاتيح Binance: \n/binance <API_KEY> <API_SECRET>\n\n"
                "لـ Kucoin: \n/kucoin <API_KEY> <API_SECRET> <PASSPHRASE>\n\n"
                "للمحفظة:\n/wallet <ADDRESS>")
        await cq.edit_message_text(text)
    elif data == "reports":
        await cq.edit_message_text("اطلب التقرير بالأوامر: /report daily|weekly|monthly")
    else:
        await cq.edit_message_text("قيد التطوير.")

# Commands to save APIs / wallet (example)
async def binance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /binance <API_KEY> <API_SECRET>")
        return
    key, secret = args
    execute("UPDATE users SET api_binance_key=%s, api_binance_secret=%s WHERE telegram_id=%s", (key, secret, tg.id))
    await update.message.reply_text("✅ تم حفظ مفاتيح Binance. يتم التحقق الآن (خلفية).")
    send_admin_alert("Binance key saved", f"User {tg.id} saved Binance keys.")

async def kucoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Usage: /kucoin <API_KEY> <API_SECRET> <PASSPHRASE>")
        return
    key, secret, passp = args
    execute("UPDATE users SET api_kucoin_key=%s, api_kucoin_secret=%s, api_kucoin_pass=%s WHERE telegram_id=%s", (key, secret, passp, tg.id))
    await update.message.reply_text("✅ تم حفظ مفاتيح Kucoin.")
    send_admin_alert("Kucoin key saved", f"User {tg.id} saved Kucoin keys.")

async def wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Usage: /wallet <ADDRESS>")
        return
    addr = args[0]
    execute("UPDATE users SET wallet_address=%s WHERE telegram_id=%s", (addr, tg.id))
    await update.message.reply_text("✅ تم حفظ عنوان المحفظة.")
