# db/encryption.py
import os
from cryptography.fernet import Fernet

# قراءة مفتاح التشفير من متغير البيئة
KEY = os.getenv("ENCRYPTION_KEY")

# التحقق من وجود المفتاح
if not KEY:
    raise ValueError("خطأ: متغير البيئة ENCRYPTION_KEY غير معرف!")

# إنشاء كائن Fernet للتشفير وفك التشفير
fernet = Fernet(KEY.encode())

# دوال مساعدة للتشفير وفك التشفير
def encrypt_value(value: str) -> str:
    """
    تشفير قيمة نصية.
    """
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    """
    فك تشفير قيمة نصية.
    """
    return fernet.decrypt(value.encode()).decode()