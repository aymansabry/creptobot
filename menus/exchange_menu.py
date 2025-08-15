from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def exchange_selection_keyboard():
    platforms = [
        "Binance", "Bybit", "KuCoin", "Huobi", "OKX",
        "Bitget", "Gate.io", "Kraken", "Coinbase", "Bitfinex"
    ]
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(name, callback_data=f"select_{name.lower()}") for name in platforms]
    kb.add(*buttons)
    return kb