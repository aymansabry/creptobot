from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()

# لوحة المفاتيح الرئيسية
def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="💰 إنشاء محفظة"),
        types.KeyboardButton(text="📊 عرض الصفقات"),
        types.KeyboardButton(text="👤 حسابي")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "مرحباً بك في بوت التداول الذكي! 🚀\n"
        "اختر أحد الخيارات من القائمة:",
        reply_markup=main_keyboard()
    )

@router.message(F.text == "💰 إنشاء محفظة")
async def create_wallet(message: types.Message):
    # هنا كود إنشاء المحفظة الفعلي
    await message.answer("تم إنشاء محفظتك بنجاح! 🎉\n\nالعنوان: TXXXX...XXXX")

@router.message(F.text == "📊 عرض الصفقات")
async def show_deals(message: types.Message):
    # هنا كود عرض الصفقات
    await message.answer("أفضل الصفقات المتاحة الآن:\n\n1. صفقة BTC/USDT - ربح 2.5%")

@router.message(F.text == "👤 حسابي")
async def my_account(message: types.Message):
    # هنا كود عرض بيانات الحساب
    await message.answer("رصيدك الحالي: 1000 USDT\n\nالصفقات النشطة: 3")
