from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from db.session import AsyncSessionLocal
from db.models import User, ApiKey, AccountSetting
import asyncio
from config import settings
from api.app import register, add_keys, start, stop

# Reply keyboard (fixed) in Arabic
KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton('▶️ بدء التداول'), KeyboardButton('⏹ إيقاف التداول')],
    [KeyboardButton('💰 الأرباح اليومية'), KeyboardButton('⚙️ الإعدادات')],
    [KeyboardButton('📊 حالة السوق')]
], resize_keyboard=True)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('أهلاً! هذه قائمة الخيارات:', reply_markup=KEYBOARD)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    chat_id = update.message.chat_id
    # Map buttons to actions (simple handlers)
    if txt == '▶️ بدء التداول':
        await update.message.reply_text('أرسل اسم المستخدم لربط حسابك (مثال: ayman):', reply_markup=None)
        # next message should be username; minimal flow omitted for brevity
    elif txt == '⏹ إيقاف التداول':
        await update.message.reply_text('جارٍ إيقاف التداول...', reply_markup=KEYBOARD)
    elif txt == '💰 الأرباح اليومية':
        await update.message.reply_text('جارٍ استرجاع الأرباح...', reply_markup=KEYBOARD)
    elif txt == '⚙️ الإعدادات':
        await update.message.reply_text('⚙️ إعدادات:\n- 🔑 ربط حساب بينانس\n- 💵 تحديد مبلغ التداول\n- 🪙 الحد الأدنى لـ BNB', reply_markup=KEYBOARD)
    elif txt == '📊 حالة السوق':
        await update.message.reply_text('جارٍ تحضير ملخّص السوق...', reply_markup=KEYBOARD)
    else:
        await update.message.reply_text('اختار أحد الأزرار من اللوحة أسفل الشاشة.', reply_markup=KEYBOARD)

def run_telegram_bot():
    token = settings.telegram_bot_token
    if not token:
        print('Telegram token not configured.')
        return
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()
