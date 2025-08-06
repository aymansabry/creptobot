import random
import string

def generate_virtual_wallet_address() -> str:
    prefix = "0x"
    random_part = ''.join(random.choices(string.hexdigits.lower(), k=40))
    return prefix + random_part
