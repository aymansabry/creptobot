from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from services.database import Database
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=Config.USER_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database()

class InvestmentStates(StatesGroup):
    waiting_amount = State()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💰 إدارة الاستثمار", callback_data="manage_investment"),
        types.InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")
    )
    await message.answer("مرحباً بك في نظام إدارة الاستثمار الآلي", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'manage_investment')
async def manage_investment(callback: types.CallbackQuery):
    investment = db.get_investment(callback.from_user.id)
    status = "🟢 نشط" if investment['is_active'] else "🔴 متوقف"
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(f"المبلغ: {investment['amount']} USDT", callback_data="set_amount"),
        types.InlineKeyboardButton(f"الحالة: {status}", callback_data="toggle_status"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
    )
    await callback.message.edit_text("إدارة الاستثمار:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'set_amount')
async def set_amount(callback: types.CallbackQuery):
    await InvestmentStates.waiting_amount.set()
    await callback.message.edit_text("أدخل مبلغ الاستثمار بالـ USDT:")

@dp.message_handler(state=InvestmentStates.waiting_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount > 0:
            if db.set_investment(message.from_user.id, amount):
                await message.answer(f"✅ تم تعيين مبلغ الاستثمار إلى {amount} USDT")
            else:
                await message.answer("❌ حدث خطأ أثناء حفظ المبلغ")
        else:
            await message.answer("❌ المبلغ يجب أن يكون أكبر من الصفر")
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح")
    
    await state.finish()
    await manage_investment(await bot.send_message(message.from_user.id, "جاري التحديث..."))

@dp.callback_query_handler(lambda c: c.data == 'toggle_status')
async def toggle_status(callback: types.CallbackQuery):
    new_status = db.toggle_investment(callback.from_user.id)
    status = "🟢 نشط" if new_status else "🔴 متوقف"
    await callback.answer(f"تم تغيير الحالة إلى: {status}")
    await manage_investment(callback)

@dp.callback_query_handler(lambda c: c.data == 'help')
async def show_help(callback: types.CallbackQuery):
    help_text = """
💰 دليل إدارة الاستثمار:

1. تعيين المبلغ:
- اضغط على زر المبلغ
- أدخل المبلغ بالـ USDT

2. تبديل الحالة:
- تشغيل/إيقاف النظام الآلي

للدعم الفني: @YourSupportBot
"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
    await callback.message.edit_text(help_text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back_to_main')
async def back_to_main(callback: types.CallbackQuery):
    await start(callback.message)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
