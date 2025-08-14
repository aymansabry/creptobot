import os
from cryptography.fernet import Fernet

# الحصول على المفتاح من البيئة
KEY = os.environ.get("ENCRYPTION_KEY")

# التأكد من أن المفتاح موجود
if not KEY:
    raise ValueError("ENCRYPTION_KEY غير معرف في متغيرات البيئة!")

# تهيئة Fernet
fernet = Fernet(KEY.encode())

# دوال التشفير وفك التشفير
def encrypt_value(value: str) -> str:
    """تشفير نص"""
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    """فك التشفير"""
    return fernet.decrypt(value.encode()).decode()
