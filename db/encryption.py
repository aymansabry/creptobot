import os
from cryptography.fernet import Fernet

KEY = os.environ.get("ENCRYPTION_KEY")
if not KEY:
    raise ValueError("ENCRYPTION_KEY not defined in environment variables!")

fernet = Fernet(KEY.encode())

def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()