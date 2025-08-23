import os
import logging
import httpx
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BASE = os.getenv('API_BASE_URL', 'http://127.0.0.1:8080')
if not BOT_TOKEN:
    raise ValueError('TELEGRAM_BOT_TOKEN must be set')

app = Application.builder().token(BOT_TOKEN).build()

MAIN_MENU = [
    ['📊 حالة السوق', '💰 بدء التداول'],
    ['📜 التقارير', '⚙️ الإعدادات'],
    ['🛑 إيقاف التداول']
]
keyboard = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

A_WAITING_SETTINGS = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_BASE}/whoami", params={'chat_id': chat_id})
        if r.status_code == 200 and r.json().get('found'):
            context.user_data['user_id'] = r.json()['user_id']
            await update.message.reply_text('✅ تم تسجيل دخولك مسبقًا.', reply_markup=keyboard)
        else:
            payload = {'username': update.effective_user.username or f'user_{chat_id}', 'telegram_chat_id': str(chat_id)}
            r2 = await client.post(f"{API_BASE}/register", json=payload)
            if r2.status_code == 200:
                data = r2.json()
                context.user_data['user_id'] = data.get('user_id')
                await update.message.reply_text('✅ تم التسجيل بنجاح، افتح الإعدادات لإضافة مفاتيح Binance والمبلغ.', reply_markup=keyboard)
            else:
                await update.message.reply_text('خطأ في التسجيل. حاول لاحقًا.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/start - القائمة\n/help - المساعدة')

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('أرسل المفاتيح وتفاصيل التداول بهذا الشكل (CSV):\nAPI_KEY,API_SECRET,AMOUNT_USDT\nأو أرسل "skip" للرجوع', reply_markup=ReplyKeyboardRemove())
    return A_WAITING_SETTINGS

async def settings_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = context.user_data.get('user_id')
    if not user_id:
        await update.message.reply_text('لم يتم التعرف على حسابك. أرسل /start أولاً.', reply_markup=keyboard)
        return ConversationHandler.END
    if text.lower() == 'skip':
        await update.message.reply_text('تم إلغاء الإعدادات.', reply_markup=keyboard)
        return ConversationHandler.END
    parts = [p.strip() for p in text.split(',')]
    if len(parts) < 3:
        await update.message.reply_text('صيغة خاطئة. أرسل: API_KEY,API_SECRET,AMOUNT_USDT', reply_markup=keyboard)
        return ConversationHandler.END
    api_key, api_secret, amount = parts[0], parts[1], float(parts[2])
    payload = {'user_id': user_id, 'api_key': api_key, 'api_secret': api_secret, 'trading_amount_usdt': amount}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{API_BASE}/settings", json=payload)
        if r.status_code == 200:
            await update.message.reply_text('✅ تم حفظ الإعدادات بنجاح.', reply_markup=keyboard)
        else:
            await update.message.reply_text(f'فشل حفظ الإعدادات: {r.text}', reply_markup=keyboard)
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = context.user_data.get('user_id')
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            if text == '📊 حالة السوق':
                r = await client.get(f"{API_BASE}/market_summary")
                await update.message.reply_text(r.text if r.status_code==200 else str(r.text), reply_markup=keyboard)
            elif text == '💰 بدء التداول':
                if not user_id:
                    await update.message.reply_text('أرسل /start للتسجيل أولاً.', reply_markup=keyboard)
                    return
                payload = {'user_id': user_id, 'trade_amount_usdt':  context.user_data.get('trade_amount_usdt', 0) or 10}
                r = await client.post(f"{API_BASE}/start", json=payload)
                await update.message.reply_text('تم طلب بدء التداول.' if r.status_code==200 else f'فشل: {r.text}', reply_markup=keyboard)
            elif text == '📜 التقارير':
                if not user_id:
                    await update.message.reply_text('أرسل /start للتسجيل أولاً.', reply_markup=keyboard)
                    return
                r = await client.get(f"{API_BASE}/report", params={'user_id': user_id})
                await update.message.reply_text(r.text if r.status_code==200 else str(r.text), reply_markup=keyboard)
            elif text == '⚙️ الإعدادات':
                return await settings_cmd(update, context)
            elif text == '🛑 إيقاف التداول':
                if not user_id:
                    await update.message.reply_text('أرسل /start للتسجيل أولاً.', reply_markup=keyboard)
                    return
                payload = {'user_id': user_id}
                r = await client.post(f"{API_BASE}/stop", json=payload)
                await update.message.reply_text('تم إيقاف التداول.' if r.status_code==200 else f'فشل الإيقاف: {r.text}', reply_markup=keyboard)
            else:
                await update.message.reply_text('اختر من القائمة أو استخدم /start.', reply_markup=keyboard)
        except Exception as e:
            logger.exception('Error handling message')
            await update.message.reply_text(f'حدث خطأ: {e}', reply_markup=keyboard)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('settings', settings_cmd)],
    states={A_WAITING_SETTINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_receive)]},
    fallbacks=[]
)

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('help', help_command))
app.add_handler(conv_handler)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
