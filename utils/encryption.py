from cryptography.fernet import Fernet
from core.config import ENCRYPTION_KEY

class EncryptionService:
    def __init__(self):
        self.cipher = Fernet(ENCRYPTION_KEY.encode())

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        return self.cipher.decrypt(data.encode()).decode()
