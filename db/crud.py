from sqlalchemy.orm import Session
from .models import User, UserWallet, SystemSettings
from datetime import datetime

def get_user(db: Session, telegram_id: int):
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int, username: str):
    db_user = User(telegram_id=telegram_id, username=username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_wallet(db: Session, user_id: int, wallet_type: str):
    wallet = UserWallet(user_id=user_id, wallet_type=wallet_type)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

def get_system_settings(db: Session):
    return db.query(SystemSettings).first()
