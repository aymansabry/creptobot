# validation.py
from binance_api import BinanceAPI
from kucoin_api import KucoinAPI
import re

def validate_wallet_address(address):
    # generic lightweight validation: length + hex/check
    if not address or len(address) < 26 or len(address) > 64:
        return False, "العنوان قصير/طويل جداً"
    # simple alnum check
    if not re.match(r'^[A-Za-z0-9]+$', address.replace('0x','')):
        return True, "يبدو صالحًا (تحقق من نوع الشبكة)."
    return True, "يبدو صالحاً."

def validate_binance_api(key, secret):
    try:
        c = BinanceAPI(key, secret)
        bal = c.get_account_balance('USDT')
        return True, "مفتاح Binance صالح."
    except Exception as e:
        return False, f"فشل التحقق من Binance: {str(e)}"

def validate_kucoin_api(key, secret, passphrase):
    try:
        c = KucoinAPI(key, secret, passphrase)
        bal = c.get_account_balance('USDT')
        return True, "مفتاح Kucoin صالح."
    except Exception as e:
        return False, f"فشل التحقق من Kucoin: {str(e)}"

def api_guides():
    return {
        "binance": "Binance API:\n1. سجل دخول Binance -> API Management -> Create API\n2. فعّل \"Trade\" و\"Enable Reading\"\n3. انسخ API Key و Secret وألصقهما هنا.",
        "kucoin": "Kucoin API:\n1. سجل دخول Kucoin -> API Management -> Create API\n2. احفظ Key, Secret و Passphrase.\n3. فعّل صلاحيات التداول والقراءة.",
        "wallet": "Wallet address:\nانسخ عنوان الاستلام من محفظتك (مثلاً TrustWallet أو Binance). تأكد من الشبكة (ERC20 / TRC20)."
    }
