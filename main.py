from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import Database, ExchangePlatform, User, ExchangeConnection
from config import Config
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة البوت
bot = Bot(token=Config.USER_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database()

# حالات المستخدم
class UserStates(StatesGroup):
    waiting_exchange = State()
    waiting_api_key = State()
    waiting_api_secret = State()
    waiting_passphrase = State()
    waiting_investment = State()
    waiting_report_date = State()
    waiting_confirmation = State()

# ---- وظائف مساعدة ----
async def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📊 بيانات التداول", "💰 إدارة الاستثمار")
    keyboard.row("📈 حالة السوق", "📅 كشف حساب")
    return keyboard

async def show_main_menu(message: types.Message):
    keyboard = await get_main_keyboard()
    await message.answer("القائمة الرئيسية:", reply_markup=keyboard)

# ---- معالجة الأوامر والرسائل ----
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    try:
        user = db.get_user(message.from_user.id)
        if not user:
            user_data = {
                'telegram_id': message.from_user.id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'balance': 0.0,
                'demo_balance': 10000.0
            }
            db.add_user(user_data)
        
        await show_main_menu(message)
    except Exception as e:
        logger.error(f"خطأ في أمر /start: {e}")
        await message.answer("❌ حدث خطأ أثناء معالجة طلبك، يرجى المحاولة لاحقاً")

@dp.message_handler(text="📊 بيانات التداول")
async def trading_data(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("➕ ربط منصة جديدة", callback_data="connect_exchange"),
        types.InlineKeyboardButton("⚙️ إدارة المنصات", callback_data="manage_exchanges"),
        types.InlineKeyboardButton("👛 رصيد المحفظة", callback_data="wallet_balance")
    )
    await message.answer("إدارة بيانات التداول:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "connect_exchange")
async def connect_exchange(callback: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    for platform in ExchangePlatform:
        keyboard.add(types.InlineKeyboardButton(
            text=platform.value.upper(),
            callback_data=f"select_{platform.value}"
        ))
    await callback.message.edit_text("اختر المنصة لربطها:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("select_"))
async def select_exchange(callback: types.CallbackQuery, state: FSMContext):
    platform = callback.data.split("_")[1]
    async with state.proxy() as data:
        data['platform'] = platform
    await UserStates.waiting_api_key.set()
    await callback.message.edit_text(f"أدخل مفتاح API لـ {platform.upper()}:")

@dp.message_handler(state=UserStates.waiting_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_key'] = message.text
    await UserStates.next()
    await message.answer("أدخل السر السري (API Secret):")

@dp.message_handler(state=UserStates.waiting_api_secret)
async def process_api_secret(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_secret'] = message.text
        platform = data['platform']
    
    if platform == 'kucoin':
        await UserStates.next()
        await message.answer("أدخل كلمة المرور (Passphrase) الخاصة بـ KuCoin:")
    else:
        await save_connection(message, state)

@dp.message_handler(state=UserStates.waiting_passphrase)
async def process_passphrase(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['passphrase'] = message.text
    await save_connection(message, state)

async def save_connection(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            user_id = message.from_user.id
            platform = data['platform']
            api_key = data['api_key']
            api_secret = data['api_secret']
            passphrase = data.get('passphrase')
            
            success = db.add_exchange_connection(
                user_id=user_id,
                platform=platform,
                api_key=api_key,
                api_secret=api_secret,
                passphrase=passphrase
            )
            
            if success:
                await message.answer(f"✅ تم ربط {platform.upper()} بنجاح!", reply_markup=await get_main_keyboard())
            else:
                await message.answer("❌ فشل في ربط المنصة، يرجى المحاولة لاحقاً")
    except Exception as e:
        logger.error(f"خطأ في حفظ اتصال المنصة: {e}")
        await message.answer("❌ حدث خطأ أثناء معالجة طلبك")
    finally:
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == "manage_exchanges")
async def manage_exchanges(callback: types.CallbackQuery):
    try:
        connections = db.get_user_connections(callback.from_user.id)
        if not connections:
            await callback.answer("ليس لديك أي منصات مرتبطة")
            return
        
        keyboard = types.InlineKeyboardMarkup()
        for conn in connections:
            status = "🟢" if conn['is_active'] else "🔴"
            keyboard.add(types.InlineKeyboardButton(
                text=f"{status} {conn['platform'].upper()}",
                callback_data=f"manage_{conn['id']}"
            ))
        keyboard.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
        await callback.message.edit_text("اختر المنصة لإدارتها:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في إدارة المنصات: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data.startswith("manage_"))
async def manage_single_exchange(callback: types.CallbackQuery):
    try:
        conn_id = int(callback.data.split("_")[1])
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🔄 تفعيل/إيقاف", callback_data=f"toggle_{conn_id}"),
            types.InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_{conn_id}"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="manage_exchanges")
        )
        await callback.message.edit_text("إدارة المنصة:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في إدارة المنصة الفردية: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data.startswith("toggle_"))
async def toggle_connection(callback: types.CallbackQuery):
    try:
        conn_id = int(callback.data.split("_")[1])
        success = db.toggle_connection_status(conn_id)
        if success:
            await callback.answer("تم تغيير حالة المنصة")
            await manage_exchanges(callback)
        else:
            await callback.answer("❌ فشل في تغيير الحالة")
    except Exception as e:
        logger.error(f"خطأ في تبديل حالة الاتصال: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data.startswith("delete_"))
async def delete_connection(callback: types.CallbackQuery):
    try:
        conn_id = int(callback.data.split("_")[1])
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ نعم", callback_data=f"confirm_delete_{conn_id}"),
            types.InlineKeyboardButton("❌ لا", callback_data="manage_exchanges")
        )
        await callback.message.edit_text("هل أنت متأكد من حذف هذه المنصة؟", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في حذف الاتصال: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data.startswith("confirm_delete_"))
async def confirm_delete(callback: types.CallbackQuery):
    try:
        conn_id = int(callback.data.split("_")[2])
        success = db.delete_connection(conn_id)
        if success:
            await callback.answer("تم حذف المنصة بنجاح")
        else:
            await callback.answer("❌ فشل في حذف المنصة")
        await manage_exchanges(callback)
    except Exception as e:
        logger.error(f"خطأ في تأكيد الحذف: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.message_handler(text="💰 إدارة الاستثمار")
async def manage_investment(message: types.Message):
    try:
        user = db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ لم يتم العثور على بيانات المستخدم")
            return
        
        status = "🟢 نشط" if user.is_active else "🔴 متوقف"
        mode = "وهمي" if user.mode == 'demo' else "حقيقي"
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton(f"💵 المبلغ: {user.investment_amount:.2f} USDT", callback_data="set_amount"),
            types.InlineKeyboardButton(f"🚀 الحالة: {status}", callback_data="toggle_status"),
            types.InlineKeyboardButton(f"🔄 الوضع: {mode}", callback_data="toggle_mode"),
            types.InlineKeyboardButton("▶️ بدء التداول", callback_data="start_trading"),
            types.InlineKeyboardButton("⏹️ إيقاف التداول", callback_data="stop_trading"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
        )
        await message.answer("إدارة الاستثمار:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في إدارة الاستثمار: {e}")
        await message.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data == "set_amount")
async def set_amount(callback: types.CallbackQuery):
    await UserStates.waiting_investment.set()
    await callback.message.edit_text("أدخل مبلغ الاستثمار بالـ USDT:")

@dp.message_handler(state=UserStates.waiting_investment)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        user = db.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ لم يتم العثور على بيانات المستخدم")
            await state.finish()
            return
            
        if amount >= Config.MIN_INVESTMENT:
            if (user.mode == 'live' and user.balance >= amount) or (user.mode == 'demo' and user.demo_balance >= amount):
                db.set_investment_amount(message.from_user.id, amount)
                await message.answer(f"✅ تم تعيين مبلغ الاستثمار إلى {amount} USDT")
            else:
                await message.answer(f"❌ رصيدك لا يكفي، يرجى إيداع المزيد من الأموال")
        else:
            await message.answer(f"❌ الحد الأدنى للاستثمار هو {Config.MIN_INVESTMENT} USDT")
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح")
    except Exception as e:
        logger.error(f"خطأ في معالجة مبلغ الاستثمار: {e}")
        await message.answer("❌ حدث خطأ أثناء معالجة طلبك")
    finally:
        await state.finish()
        await manage_investment(message)

@dp.callback_query_handler(lambda c: c.data == "toggle_status")
async def toggle_status(callback: types.CallbackQuery):
    try:
        new_status = db.toggle_trading_status(callback.from_user.id)
        status = "🟢 نشط" if new_status else "🔴 متوقف"
        await callback.answer(f"تم تغيير الحالة إلى: {status}")
        await manage_investment(callback.message)
    except Exception as e:
        logger.error(f"خطأ في تبديل حالة التداول: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data == "toggle_mode")
async def toggle_mode(callback: types.CallbackQuery):
    try:
        new_mode = db.toggle_trading_mode(callback.from_user.id)
        mode = "وهمي" if new_mode == 'demo' else "حقيقي"
        await callback.answer(f"تم تغيير الوضع إلى: {mode}")
        await manage_investment(callback.message)
    except Exception as e:
        logger.error(f"خطأ في تبديل وضع التداول: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data == "start_trading")
async def start_trading(callback: types.CallbackQuery):
    try:
        user = db.get_user(callback.from_user.id)
        if not user:
            await callback.answer("❌ لم يتم العثور على بيانات المستخدم")
            return
        
        if user.investment_amount <= 0:
            await callback.answer("❌ يرجى تعيين مبلغ الاستثمار أولاً")
            return
        
        connections = db.get_user_connections(callback.from_user.id)
        if len(connections) < 2:
            await callback.answer("❌ تحتاج إلى ربط منصتين على الأقل")
            return
        
        db.toggle_trading_status(callback.from_user.id)
        await callback.answer("🚀 بدأ التداول الآلي بنجاح")
        await manage_investment(callback.message)
    except Exception as e:
        logger.error(f"خطأ في بدء التداول: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data == "stop_trading")
async def stop_trading(callback: types.CallbackQuery):
    try:
        db.toggle_trading_status(callback.from_user.id)
        await callback.answer("⏹️ تم إيقاف التداول الآلي")
        await manage_investment(callback.message)
    except Exception as e:
        logger.error(f"خطأ في إيقاف التداول: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.message_handler(text="📈 حالة السوق")
async def market_status(message: types.Message):
    try:
        opportunities = db.get_recent_opportunities(5)
        if not opportunities:
            await message.answer("لا توجد فرص مراجحة حالياً")
            return
        
        text = "📊 أفضل فرص المراجحة:\n\n"
        for opp in opportunities:
            text += (
                f"🔹 {opp['symbol']}\n"
                f"شراء من: {opp['buy_exchange']} بسعر: {opp['buy_price']:.4f}\n"
                f"بيع في: {opp['sell_exchange']} بسعر: {opp['sell_price']:.4f}\n"
                f"الربح: {opp['profit_percentage']:.2f}%\n"
                f"──────────────────\n"
            )
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_market"))
        await message.answer(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في عرض حالة السوق: {e}")
        await message.answer("❌ حدث خطأ أثناء معالجة طلبك")

@dp.callback_query_handler(lambda c: c.data == "refresh_market")
async def refresh_market(callback: types.CallbackQuery):
    await callback.answer("جارٍ تحديث البيانات...")
    await market_status(callback.message)

@dp.message_handler(text="📅 كشف حساب")
async def account_statement(message: types.Message):
    await UserStates.waiting_report_date.set()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🕒 آخر 7 أيام", callback_data="report_7"),
        types.InlineKeyboardButton("🕒 آخر 30 يوم", callback_data="report_30"),
        types.InlineKeyboardButton("🕒 الكل", callback_data="report_all")
    )
    await message.answer("اختر الفترة الزمنية:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("report_"), state=UserStates.waiting_report_date)
async def generate_report(callback: types.CallbackQuery, state: FSMContext):
    try:
        period = callback.data.split("_")[1]
        days = 7 if period == '7' else 30 if period == '30' else None
        
        transactions = db.get_user_transactions(callback.from_user.id, days)
        if not transactions:
            await callback.answer("لا توجد معاملات في هذه الفترة")
            return
        
        total_profit = sum(t['profit'] for t in transactions if t['profit'] is not None)
        text = f"📅 كشف حساب ({'آخر ' + str(days) + ' أيام' if days else 'الكل'})\n\n"
        text += f"🔹 إجمالي الربح: {total_profit:.4f} USDT\n"
        text += f"🔹 عدد المعاملات: {len(transactions)}\n\n"
        
        for t in transactions[:10]:  # عرض آخر 10 معاملات فقط
            profit = t['profit'] if t['profit'] is not None else 0.0
            text += (
                f"📌 {t['platform']} - {t['symbol']}\n"
                f"المبلغ: {t['amount']:.4f} | الربح: {profit:.4f}\n"
                f"النوع: {t['type']} | التاريخ: {t['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                f"──────────────────\n"
            )
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("📤 تصدير كـ CSV", callback_data=f"export_{period}"))
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"خطأ في إنشاء التقرير: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة طلبك")
    finally:
        await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith("export_"))
async def export_report(callback: types.CallbackQuery):
    await callback.answer("سيتم إرسال ملف CSV قريباً...")
    # هنا يتم إنشاء وإرسال ملف CSV
    await callback.message.answer("سيصلك ملف كشف الحساب قريباً")

@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await show_main_menu(callback.message)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
