from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from constants import BUTTONS

def main_menu(role="user"):
    buttons = [
        [KeyboardButton(text=BUTTONS["invest_auto"]), KeyboardButton(text=BUTTONS["invest_manual"])],
        [KeyboardButton(text=BUTTONS["withdraw"]), KeyboardButton(text=BUTTONS["support"])]
    ]
    if role == "admin":
        buttons.append([KeyboardButton(text=BUTTONS["dashboard"])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def admin_menu():
    buttons = [
        [KeyboardButton(text="📊 إحصائيات الصفقات")],
        [KeyboardButton(text=BUTTONS["back"])]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS["invest_auto"])],
            [KeyboardButton(text=BUTTONS["withdraw"])],
            [KeyboardButton(text=BUTTONS["support"])]
        ],
        resize_keyboard=True
    )
