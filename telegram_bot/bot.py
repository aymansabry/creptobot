import os
import logging
import httpx
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError('TELEGRAM_BOT_TOKEN must be set')

app = Application.builder().token(BOT_TOKEN).build()

main_menu = [
    ['📊 حالة السوق', '💰 بدء التداول'],
    ['📜 التقارير', '⚙️ الإعدادات'],
    ['🛑 إيقاف التداول']
]
keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
API_BASE = os.getenv('API_BASE_URL', 'http://127.0.0.1:8080')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('✅ أهلاً! اختر من القائمة:', reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/start - القائمة\n/help - المساعدة')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            if text == '📊 حالة السوق':
                r = await client.get(f"{API_BASE}/market_summary")
                await update.message.reply_text(r.text, reply_markup=keyboard)
            elif text == '💰 بدء التداول':
                await update.message.reply_text('أرسل رقم المستخدم (user_id) لبدء التداول:', reply_markup=None)
            elif text.isdigit():
                payload = {'user_id': int(text), 'trade_amount_usdt': 10}
                r = await client.post(f"{API_BASE}/start", json=payload)
                await update.message.reply_text(r.text if r.status_code==200 else str(r.text), reply_markup=keyboard)
            elif text == '📜 التقارير':
                r = await client.get(f"{API_BASE}/report?user_id=1")
                await update.message.reply_text(r.text, reply_markup=keyboard)
            elif text == '⚙️ الإعدادات':
                r = await client.get(f"{API_BASE}/settings?user_id=1")
                await update.message.reply_text(r.text, reply_markup=keyboard)
            elif text == '🛑 إيقاف التداول':
                await update.message.reply_text('أرسل رقم المستخدم (user_id) لإيقاف التداول:', reply_markup=None)
            else:
                await update.message.reply_text('اختر زر من القائمة أو أرسل user_id', reply_markup=keyboard)
        except Exception as e:
            logger.exception('Error handling message')
            await update.message.reply_text(f'حدث خطأ: {e}', reply_markup=keyboard)

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('help', help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
