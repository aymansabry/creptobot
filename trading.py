import time
import random
from cryptography.fernet import Fernet
from database import SessionLocal
from models import User

# مفتاح التشفير (لازم يكون نفس الموجود في handlers)
FERNET_KEY = Fernet.generate_key()
fernet = Fernet(FERNET_KEY)

# تشفير القيم
def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

# فك التشفير
def decrypt_value(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()

# تحليل السوق (محاكاة بسيطة)
def analyze_market() -> str:
    trends = ["📈 السوق في اتجاه صاعد", "📉 السوق في اتجاه هابط", "⚖️ السوق متذبذب"]
    signal = random.choice(trends)
    confidence = random.randint(70, 95)
    return f"{signal}\n📊 نسبة الثقة: {confidence}%"

# محاكاة المراجحة والتداول
async def start_trading(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()

    if not user:
        db.close()
        return

    for _ in range(5):  # تحديث 5 مرات كمثال
        time.sleep(2)  # تأخير بسيط لمحاكاة الوقت الحقيقي

        # ربح عشوائي بين 0.2% و 1%
        profit_percent = random.uniform(0.2, 1)
        profit_amount = user.balance * (profit_percent / 100)

        user.balance += profit_amount
        user.profits += profit_amount
        db.commit()

        print(f"[TRADING] المستخدم {user_id} | ربح: {profit_amount:.2f}$ | الرصيد: {user.balance:.2f}$")

    db.close()
