import re

def is_valid_amount(text: str):
    try:
        value = float(text)
        return value >= 10.0
    except ValueError:
        return False

def is_valid_wallet(text: str):
    # تحقق من عنوان TRON TRC20
    return bool(re.match(r"^T[a-zA-Z0-9]{33}$", text))
