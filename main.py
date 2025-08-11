import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import Config
from services.database import Database
from services.arbitrage import ArbitrageEngine
from services.exchange_api import BinanceAPI, KuCoinAPI

# تهيئة التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة البوت
bot = Bot(token=Config.USER_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database()
arbitrage = ArbitrageEngine()

# حالات المستخدم
class UserStates(StatesGroup):
    waiting_for_binance_key = State()
    waiting_for_binance_secret = State()
    waiting_for_kucoin_key = State()
    waiting_for_kucoin_secret = State()
    waiting_for_kucoin_passphrase = State()
    waiting_for_investment_amount = State()
    waiting_for_confirmation = State()

# ---- واجهات المستخدم ----
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    
    user = db.get_user(message.from_user.id)
    if not user:
        db.add_user({
            'telegram_id': message.from_user.id,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'username': message.from_user.username
        })
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🔄 ربط منصات التداول")
    keyboard.row("💰 إدارة الاستثمار", "📊 لوحة التحكم")
    keyboard.row("ℹ️ المساعدة")
    
    await message.answer(
        "مرحباً بك في بوت التداول بالمراجحة الآلية!\n"
        "اختر من القائمة أدناه:", 
        reply_markup=keyboard
    )

@dp.message_handler(text="🔄 ربط منصات التداول")
async def connect_exchanges(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🔗 Binance", callback_data="connect_binance"),
        types.InlineKeyboardButton("🔗 KuCoin", callback_data="connect_kucoin")
    )
    await message.answer("اختر المنصة التي تريد ربطها:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('connect_'))
async def process_exchange_connection(callback_query: types.CallbackQuery, state: FSMContext):
    platform = callback_query.data.split('_')[1]
    
    if platform == 'binance':
        await UserStates.waiting_for_binance_key.set()
        await bot.send_message(
            callback_query.from_user.id,
            "أدخل مفتاح API الخاص بـ Binance:",
            reply_markup=types.ReplyKeyboardRemove()
        )
    elif platform == 'kucoin':
        await UserStates.waiting_for_kucoin_key.set()
        await bot.send_message(
            callback_query.from_user.id,
            "أدخل مفتاح API الخاص بـ KuCoin:",
            reply_markup=types.ReplyKeyboardRemove()
        )

@dp.message_handler(state=UserStates.waiting_for_binance_key)
async def process_binance_key(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['binance_key'] = message.text
    
    await UserStates.next()
    await message.answer("أدخل السر السري (Secret Key) لـ Binance:")

@dp.message_handler(state=UserStates.waiting_for_binance_secret)
async def process_binance_secret(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['binance_secret'] = message.text
        api = BinanceAPI()
        
        if api.validate_credentials(data['binance_key'], data['binance_secret']):
            encrypted_key = api.encrypt_data(data['binance_key'])
            encrypted_secret = api.encrypt_data(data['binance_secret'])
            
            db.add_exchange_connection({
                'user_id': message.from_user.id,
                'platform': 'binance',
                'api_key': encrypted_key,
                'api_secret': encrypted_secret,
                'is_valid': True
            })
            
            await message.answer("✅ تم ربط حساب Binance بنجاح!")
        else:
            await message.answer("❌ فشل التحقق من المفاتيح. يرجى التأكد وإعادة المحاولة.")
    
    await state.finish()

# ... (نفس المنطق لـ KuCoin مع إضافة passphrase)

@dp.message_handler(text="💰 إدارة الاستثمار")
async def manage_investment(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💵 تعيين المبلغ", callback_data="set_amount"),
        types.InlineKeyboardButton("🚀 بدء التداول", callback_data="start_trading"),
        types.InlineKeyboardButton("🛑 إيقاف التداول", callback_data="stop_trading"),
        types.InlineKeyboardButton("📈 الوضع التجريبي", callback_data="toggle_demo")
    )
    
    user = db.get_user(message.from_user.id)
    status = "🟢 نشط" if user.is_active else "🔴 متوقف"
    mode = "وهمي" if user.mode == 'demo' else "حقيقي"
    
    await message.answer(
        f"إعدادات الاستثمار الحالية:\n"
        f"الحالة: {status}\n"
        f"الوضع: {mode}\n"
        f"المبلغ: {user.investment_amount:.2f} USDT\n"
        "\nاختر الإجراء المطلوب:",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'start_trading')
async def start_trading(callback_query: types.CallbackQuery):
    user = db.get_user(callback_query.from_user.id)
    
    if user.investment_amount < Config.MIN_INVESTMENT:
        await bot.send_message(
            callback_query.from_user.id,
            f"المبلغ المدخل أقل من الحد الأدنى ({Config.MIN_INVESTMENT} USDT)"
        )
        return
    
    connections = db.get_active_connections(callback_query.from_user.id)
    if len(connections) < 2:
        await bot.send_message(
            callback_query.from_user.id,
            "يجب ربط منصتين على الأقل قبل البدء"
        )
        return
    
    await bot.send_message(
        callback_query.from_user.id,
        "🔎 جاري البحث عن فرص المراجحة..."
    )
    
    # هنا يتم تشغيل محرك المراجحة (عملياً يجب أن يكون في خلفية)
    credentials = {
        'binance': {'api_key': connections[0].api_key, 'api_secret': connections[0].api_secret},
        'kucoin': {'api_key': connections[1].api_key, 'api_secret': connections[1].api_secret}
    }
    
    opportunity = await arbitrage.find_opportunity('BTC/USDT', credentials)
    if opportunity:
        result = await arbitrage.execute_trade(opportunity, user.investment_amount, credentials)
        await bot.send_message(
            callback_query.from_user.id,
            f"🎉 تم تنفيذ صفقة ناجحة!\n"
            f"الربح: {result['realized_profit']:.4f} USDT\n"
            f"الرسوم: {result['fees']:.4f} USDT"
        )
    else:
        await bot.send_message(
            callback_query.from_user.id,
            "⚠️ لم يتم العثور على فرص مراجحة مناسبة حالياً"
        )

# ---- لوحة المدير ----
@dp.message_handler(commands=['admin'], user_id=Config.ADMIN_IDS)
async def admin_panel(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("👥 إحصاءات المستخدمين", callback_data="admin_stats"),
        types.InlineKeyboardButton("📊 تقارير التداول", callback_data="admin_reports"),
        types.InlineKeyboardButton("⚙️ إعدادات النظام", callback_data="admin_settings")
    )
    
    await message.answer("لوحة تحكم المدير:", reply_markup=keyboard)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
