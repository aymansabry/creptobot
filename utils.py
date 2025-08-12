# utils.py
import ccxt
import database

# النسبة الافتراضية لعمولة البوت
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))

# --- إنشاء كائن منصة (Exchange Object) ---
def get_exchange_client(exchange_name, api_key, api_secret, sandbox=False):
    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True
    })

    if sandbox and hasattr(exchange, "set_sandbox_mode"):
        exchange.set_sandbox_mode(True)

    return exchange

# --- جلب precision للرمز ---
def get_symbol_precision(exchange, symbol):
    markets = exchange.load_markets()
    if symbol in markets:
        market = markets[symbol]
        amount_prec = market['precision'].get('amount', 8)
        price_prec = market['precision'].get('price', 8)
        return amount_prec, price_prec
    return 8, 8

# --- تنفيذ أمر شراء ---
def place_market_buy(exchange, symbol, amount):
    amount_prec, _ = get_symbol_precision(exchange, symbol)
    amount = round(amount, amount_prec)
    order = exchange.create_market_buy_order(symbol, amount)
    return order

# --- تنفيذ أمر بيع ---
def place_market_sell(exchange, symbol, amount):
    amount_prec, _ = get_symbol_precision(exchange, symbol)
    amount = round(amount, amount_prec)
    order = exchange.create_market_sell_order(symbol, amount)
    return order

# --- تجربة تنفيذ أمر (Test Mode) ---
def test_trade(exchange, symbol, amount, side):
    print(f"[SANDBOX] {side.upper()} {amount} {symbol}")
    return {
        "id": "test-order-123",
        "symbol": symbol,
        "side": side,
        "amount": amount,
        "status": "filled"
    }

# --- تنفيذ صفقة ---
def execute_trade(telegram_id, symbol, amount, side="buy", test_only=False):
    exchanges = database.get_user_exchanges(telegram_id)
    results = []

    for ex in exchanges:
        client = get_exchange_client(ex['name'], ex['api_key'], ex['api_secret'], sandbox=ex['sandbox'])

        if test_only or ex['sandbox']:
            result = test_trade(client, symbol, amount, side)
        else:
            if side == "buy":
                result = place_market_buy(client, symbol, amount)
            else:
                result = place_market_sell(client, symbol, amount)

        results.append({"exchange": ex['name'], "result": result})

    return results

# --- حساب العمولة ---
def calculate_bot_fee(amount):
    return round((amount * BOT_FEE_PERCENT) / 100, 8)

