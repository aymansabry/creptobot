from aiogram import types
from database import query, execute

# دالة بدء المحادثة
async def start(message: types.Message):
    await message.answer("أهلاً بك! اضغط على الزر أدناه للمتابعة.", reply_markup=get_main_keyboard())

# دالة التعامل مع أزرار البوت
async def button_handler(callback_query: types.CallbackQuery):
    data = callback_query.data

    if data == "show_data":
        rows = query("SELECT * FROM your_table")
        if rows:
            text = "\n".join([str(row) for row in rows])
        else:
            text = "لا توجد بيانات حالياً."
        await callback_query.message.answer(text)

    elif data == "add_data":
        execute("INSERT INTO your_table (column_name) VALUES ('قيمة تجريبية')")
        await callback_query.message.answer("تمت إضافة البيانات بنجاح!")

    await callback_query.answer()

# لوحة الأزرار الرئيسية
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📋 عرض البيانات", callback_data="show_data"))
    keyboard.add(types.InlineKeyboardButton("➕ إضافة بيانات", callback_data="add_data"))
    return keyboard