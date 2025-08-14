from cryptography.fernet import Fernet
import os

KEY = os.environ.get("FERNET_KEY")  # تولد مرة واحدة وتخزن في البيئة

fernet = Fernet(KEY.encode())

def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()