import random
import string

def generate_mock_wallet_address(network: str = "TRC20") -> str:
    if network == "TRC20":
        return "T" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=33))
    elif network == "ERC20":
        return "0x" + ''.join(random.choices("abcdef" + string.digits, k=40))
    return ''.join(random.choices(string.ascii_letters + string.digits, k=34))
