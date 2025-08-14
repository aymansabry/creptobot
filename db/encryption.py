from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY

if ENCRYPTION_KEY is None:
    raise ValueError("ENCRYPTION_KEY غير معرف في متغيرات البيئة")

fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()