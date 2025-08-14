from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def exchange_selection_keyboard() -> InlineKeyboardMarkup:
    platforms = [
        "Binance", "Bybit", "KuCoin", "Huobi", "OKX",
        "Bitget", "Gate.io", "Kraken", "Coinbase", "Bitfinex"
    ]
    kb = InlineKeyboardMarkup(row_width=1)  # كل زر في صف منفصل
    for name in platforms:
        kb.add(InlineKeyboardButton(text=name, callback_data=f"select_{name.lower()}"))
    return kb