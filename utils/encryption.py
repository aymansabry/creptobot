# utils/encryption.py
import os
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise SystemExit("ENCRYPTION_KEY missing in env. Generate with Fernet.generate_key().decode()")

fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_text(plain: str) -> str:
    if plain is None:
        return None
    return fernet.encrypt(plain.encode()).decode()

def decrypt_text(token: str) -> str:
    if token is None:
        return None
    return fernet.decrypt(token.encode()).decode()
