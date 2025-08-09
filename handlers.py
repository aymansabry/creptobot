# handlers.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import query, execute
from validation import validate_binance_api, validate_kucoin_api, validate_wallet_address, api_guides
from notifications import send_notification_to_user
from settings import get_setting, set_setting

ROLE_OWNER = 1
ROLE_ADMIN = 2
ROLE_USER = 3

def get_user_by_telegram_id(tid):
    return query("SELECT * FROM users WHERE telegram_id=%s", (tid,), fetchone=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing = get_user_by_telegram_id(user.id)
    if not existing:
        execute("INSERT INTO users (telegram_id, username, role_id) VALUES (%s,%s,%s)", (user.id, user.username or '', ROLE_USER))
        await update.message.reply_text(f"مرحباً {user.first_name}! تم تسجيلك.")
        # notify owner(s)
        owners = query("SELECT telegram_id FROM users WHERE role_id=%s", (ROLE_OWNER,))
        for o in owners:
            try:
                context.bot.send_message(chat_id=o['telegram_id'], text=f"تم تسجيل مستخدم جديد: {user.username or user.first_name}")
            except:
                pass
    else:
        await update.message.reply_text(f"أهلاً {user.first_name}, أنت مسجل لدينا.")
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user_by_telegram_id(user.id)
    role = u['role_id'] if u else ROLE_USER
    kb = []
    kb.append([InlineKeyboardButton("استثمار/محفظة", callback_data='invest')])
    kb.append([InlineKeyboardButton("تقارير", callback_data='reports')])
    kb.append([InlineKeyboardButton("دعم/تذكرة", callback_data='support')])
    if role in (ROLE_OWNER, ROLE_ADMIN):
        kb.append([InlineKeyboardButton("إدارة المستخدمين", callback_data='manage_users')])
        kb.append([InlineKeyboardButton("إرسال إعلان", callback_data='send_ads')])
        kb.append([InlineKeyboardButton("إعدادات", callback_data='bot_settings')])
    await update.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(kb))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    data = cq.data
    user = cq.from_user
    if data == 'invest':
        await cq.edit_message_text("خيارات الاستثمار:\n- /binanceapi <key> <secret>\n- /kucoinapi <key> <secret> <pass>\n- /wallet <address>\n- /setinvest <amount>\n- /demo on/off")
    elif data == 'reports':
        await cq.edit_message_text("التقارير متاحة عبر الأوامر: /report daily|weekly|monthly")
    elif data == 'support':
        await cq.edit_message_text("لإنشاء تذكرة: /ticket <subject>|<message>")
    elif data == 'manage_users':
        users = query("SELECT id,username,is_active,role_id FROM users")
        text = "المستخدمون:\n"
        for u in users:
            text += f"ID:{u['id']} {u['username']} - {'نشط' if u['is_active'] else 'موقوف'} - role:{u['role_id']}\n"
        await cq.edit_message_text(text)
    elif data == 'send_ads':
        await cq.edit_message_text("لإرسال إعلان استخدم الأمر: /sendads <message>")
    elif data == 'bot_settings':
        s = query("SELECT setting_key,setting_value FROM settings")
        text = "الإعدادات:\n"
        for line in s:
            text += f"{line['setting_key']} = {line['setting_value']}\n"
        await cq.edit_message_text(text)
    else:
        await cq.edit_message_text("قيد التطوير.")
