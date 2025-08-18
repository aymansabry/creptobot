from sqlalchemy.orm import Session
from . import models

def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user_data: dict):
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_exchange_api(db: Session, user_id: str, exchange: str, api_data: dict):
    db_api = db.query(models.ExchangeAPI).filter(
        models.ExchangeAPI.user_id == user_id,
        models.ExchangeAPI.exchange == exchange
    ).first()
    
    if db_api:
        for key, value in api_data.items():
            setattr(db_api, key, value)
    else:
        db_api = models.ExchangeAPI(user_id=user_id, exchange=exchange, **api_data)
        db.add(db_api)
    
    db.commit()
    return db_api

def get_sub_wallets(db: Session, user_id: str):
    return db.query(models.SubWallet).filter(models.SubWallet.user_id == user_id).all()