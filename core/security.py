from cryptography.fernet import Fernet
import base64

class SecureVault:
    def __init__(self, master_key: str):
        self.cipher = Fernet(base64.b64encode(master_key.ljust(32, b'\0')[:32]))
    
    def encrypt_key(self, private_key: str) -> str:
        return self.cipher.encrypt(private_key.encode()).decode()
    
    def decrypt_key(self, encrypted_key: str) -> str:
        return self.cipher.decrypt(encrypted_key.encode()).decode()

# Example usage:
vault = SecureVault(config.ENCRYPTION_KEY)
encrypted = vault.encrypt_key("YOUR_PRIVATE_KEY")
