from cryptography.fernet import Fernet
from core.config import ENCRYPTION_KEY, ENCRYPTION_ENABLED

class EncryptionService:
    def __init__(self):
        if ENCRYPTION_ENABLED and ENCRYPTION_KEY:
            self.cipher = Fernet(ENCRYPTION_KEY.encode())
        else:
            self.cipher = None

    def encrypt(self, data: str) -> str:
        if self.cipher:
            return self.cipher.encrypt(data.encode()).decode()
        return data

    def decrypt(self, data: str) -> str:
        if self.cipher:
            return self.cipher.decrypt(data.encode()).decode()
        return data
