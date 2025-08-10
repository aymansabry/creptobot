from settings import fernet

def encrypt_api_keys(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt_api_keys(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()