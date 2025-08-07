def generate_deposit_address():
    """إنشاء عنوان إيداع فريد لكل مستخدم"""
    from hashlib import sha256
    from datetime import datetime
    return sha256(f"{datetime.now().timestamp()}".encode()).hexdigest()[:20]
