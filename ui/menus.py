# project_root/ui/menus.py

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup
from ui.buttons import *

user_main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton(START_TRADING)],
        [KeyboardButton(VIEW_BALANCE), KeyboardButton(VIEW_PORTFOLIO)],
        [KeyboardButton(VIEW_HISTORY), KeyboardButton(HELP)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

trading_options_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton(AUTO_TRADE)],
        [KeyboardButton(MANUAL_TRADE)],
        [KeyboardButton(BACK_TO_MAIN)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

admin_main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton(VIEW_USERS), KeyboardButton(VIEW_PROFITS)],
        [KeyboardButton(VIEW_ALL_TRADES), KeyboardButton(SET_FEES)],
        [KeyboardButton(TOGGLE_USER_TRADING)],
        [KeyboardButton(BACK_TO_MAIN)]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

confirmation_keyboard = InlineKeyboardMarkup(
    [[CONFIRM_YES, CONFIRM_NO]]
)
