from cryptography.fernet import Fernet
from core.config import ENCRYPTION_KEY

fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_text(plaintext: str) -> str:
    """Encrypts plaintext to a URL-safe base64 string."""
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt_text(token: str) -> str:
    """Decrypts a URL-safe base64 string to plaintext."""
    return fernet.decrypt(token.encode()).decode()
