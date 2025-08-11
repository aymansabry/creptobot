# db_access.py
from sqlalchemy.orm import Session
from models import User
from database import SessionLocal
from typing import Optional, List

def get_user_by_telegram(db: Session, telegram_id: int) -> Optional[User]:
    return db.query(User).filter(User.telegram_id==telegram_id).first()

def create_or_get_user(telegram_id: int) -> User:
    db = SessionLocal()
    try:
        u = get_user_by_telegram(db, telegram_id)
        if u:
            return u
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()

def save_account_keys(telegram_id: int, exchange: str, api_key: str=None, api_secret: str=None, passphrase: str=None, investment_amount: float=None, mode: str=None):
    db = SessionLocal()
    try:
        user = get_user_by_telegram(db, telegram_id)
        if not user:
            user = User(telegram_id=telegram_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        if exchange.lower() == "binance":
            if api_key is not None: user.binance_api_key = api_key
            if api_secret is not None: user.binance_api_secret = api_secret
        elif exchange.lower() == "kucoin":
            if api_key is not None: user.kucoin_api_key = api_key
            if api_secret is not None: user.kucoin_api_secret = api_secret
            if passphrase is not None: user.kucoin_api_passphrase = passphrase
        if investment_amount is not None:
            user.investment_amount = investment_amount
            user.last_snapshot_balance = investment_amount if (user.last_snapshot_balance == 0) else user.last_snapshot_balance
        if mode is not None:
            user.mode = mode
        db.commit()
        return True
    finally:
        db.close()

def fetch_live_accounts() -> List[User]:
    db = SessionLocal()
    try:
        rows = db.query(User).filter(User.mode=="live").all()
        return rows
    finally:
        db.close()

def update_account_pnl(telegram_id: int, profit_loss: float):
    db = SessionLocal()
    try:
        user = get_user_by_telegram(db, telegram_id)
        if not user:
            return
        user.total_profit_loss = (user.total_profit_loss or 0.0) + profit_loss
        user.last_snapshot_balance = (user.last_snapshot_balance or 0.0) + profit_loss
        db.commit()
        return True
    finally:
        db.close()

def get_account_balance(telegram_id: int):
    db = SessionLocal()
    try:
        user = get_user_by_telegram(db, telegram_id)
        if not user:
            return {"investment":0.0,"pnl":0.0,"balance":0.0}
        inv = float(user.investment_amount or 0.0)
        pnl = float(user.total_profit_loss or 0.0)
        return {"investment": inv, "pnl": pnl, "balance": inv + pnl}
    finally:
        db.close()
