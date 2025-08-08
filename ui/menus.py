# project_root/ui/menus.py

from telegram import ReplyKeyboardMarkup
from ui.buttons import *

user_main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton(START_TRADING)],
        [KeyboardButton(VIEW_BALANCE), KeyboardButton(VIEW_HISTORY)],
        [KeyboardButton(DEPOSIT_WITHDRAW)]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

trading_options_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton(AUTO_TRADE), KeyboardButton(MANUAL_TRADE)],
        [KeyboardButton(BACK_TO_MAIN)]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

admin_main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton(VIEW_USERS), KeyboardButton(SETTINGS)],
        [KeyboardButton(SEND_ANNOUNCEMENT), KeyboardButton(VIEW_TRADES)],
        [KeyboardButton(SWITCH_TO_USER)]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# New menu for selecting trial or real trading
trade_type_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton(TRIAL_TRADE)],
        [KeyboardButton(REAL_TRADE)],
        [KeyboardButton(BACK_TO_MAIN)]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)
