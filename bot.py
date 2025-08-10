import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from database import create_tables, SessionLocal, get_user_by_telegram_id, add_user_api_keys
from settings import BOT_TOKEN, OWNER_ID
from arbitrag import start_arbitrage_for_user
from utils import encrypt_api_keys, decrypt_api_keys

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("أهلاً! البوت يعمل بنجاح. استخدم /help لرؤية الأوامر.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "/start - بدء المحادثة\n"
        "/help - عرض الأوامر\n"
        "/add_api - إضافة مفاتيح API\n"
        "/balance - عرض الرصيد\n"
        "/start_arbitrage - بدء المراجحة\n"
        "/stop_arbitrage - إيقاف المراجحة\n"
    )
    await message.reply(help_text)

# أمر خاص بالمالك فقط
@dp.message(lambda m: m.from_user.id == int(OWNER_ID))
async def owner_only(message: types.Message):
    await message.reply("مرحباً مالك البوت!")

@dp.message(Command("add_api"))
async def cmd_add_api(message: types.Message):
    # هذا مجرد مثال، في الواقع يجب استقبال المفاتيح من المستخدم بطريقة آمنة
    await message.reply("أرسل مفاتيح API بصيغة: api_key,api_secret")

@dp.message()
async def receive_api_keys(message: types.Message):
    if "," in message.text:
        api_key, api_secret = map(str.strip, message.text.split(",", 1))
        encrypted_key = encrypt_api_keys(api_key)
        encrypted_secret = encrypt_api_keys(api_secret)
        # تخزين المفاتيح في قاعدة البيانات (مثال)
        user = get_user_by_telegram_id(message.from_user.id)
        if not user:
            # إضافة مستخدم جديد
            # هنا إضافة لقاعدة البيانات مع المفاتيح المشفرة
            pass
        else:
            add_user_api_keys(user.id, encrypted_key, encrypted_secret)
        await message.reply("تم حفظ مفاتيح API الخاصة بك بنجاح.")
    else:
        await message.reply("صيغة مفاتيح API غير صحيحة، يرجى الإرسال بالشكل: api_key,api_secret")

@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    # هنا استدعاء الدالة المناسبة لجلب رصيد المستخدم
    balance = 0  # مثال مؤقت
    await message.reply(f"رصيدك الحالي: {balance} دولار")

@dp.message(Command("start_arbitrage"))
async def cmd_start_arbitrage(message: types.Message):
    started = await start_arbitrage_for_user(message.from_user.id)
    if started:
        await message.reply("تم بدء عملية المراجحة بنجاح.")
    else:
        await message.reply("لا يمكن بدء المراجحة، تحقق من إعداداتك.")

@dp.message(Command("stop_arbitrage"))
async def cmd_stop_arbitrage(message: types.Message):
    # مثال إيقاف عملية المراجحة
    await message.reply("تم إيقاف عملية المراجحة.")

async def on_startup(dispatcher):
    print("البوت بدأ العمل")

async def on_shutdown(dispatcher):
    await bot.close()
    print("البوت توقف")

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)