from cryptography.fernet import Fernet
from settings import FERNET_KEY
fernet = Fernet(FERNET_KEY.encode())

def encrypt_text(plain: str) -> str:
    return fernet.encrypt(plain.encode()).decode()

def decrypt_text(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

def validate_symbol(symbol: str) -> bool:
    return '/' not in symbol and len(symbol) > 2
