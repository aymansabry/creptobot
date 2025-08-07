from datetime import datetime
from sqlalchemy.orm import Session
from models import User, Investment, Profit, Log

# إضافة مستخدم
def create_user(db: Session, telegram_id: int, first_name: str, last_name: str = None, username: str = None):
    user = User(telegram_id=telegram_id, first_name=first_name, last_name=last_name, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# الحصول على أو إنشاء مستخدم
def get_or_create_user(db: Session, telegram_id: int, first_name: str, last_name: str = None, username: str = None):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = create_user(db, telegram_id, first_name, last_name, username)
    return user

# إضافة استثمار
def create_investment(db: Session, user_id: int, amount: float):
    investment = Investment(user_id=user_id, amount=amount, created_at=datetime.now())
    db.add(investment)
    db.commit()
    db.refresh(investment)
    return investment

# إضافة ربح
def create_profit(db: Session, user_id: int, amount: float, commission: float):
    profit = Profit(user_id=user_id, amount=amount, commission=commission, created_at=datetime.now())
    db.add(profit)
    db.commit()
    db.refresh(profit)
    return profit

# إضافة سجل
def create_log(db: Session, event: str, user_id: int = None):
    log = Log(event=event, timestamp=datetime.now(), user_id=user_id)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
