from cryptography.fernet import Fernet
import os

# تحميل أو إنشاء مفتاح التشفير
SECRET_KEY_FILE = "secret.key"

def load_or_create_key():
    """
    يقوم بتحميل مفتاح التشفير إذا كان موجود، أو إنشاؤه إذا لم يكن موجود.
    """
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(SECRET_KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

# مفتاح التشفير
SECRET_KEY = load_or_create_key()
fernet = Fernet(SECRET_KEY)

def encrypt_data(data: str) -> str:
    """
    تشفير النصوص (مثل مفاتيح API)
    """
    if not data:
        return None
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    """
    فك التشفير للنصوص
    """
    if not token:
        return None
    return fernet.decrypt(token.encode()).decode()
