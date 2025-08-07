from sqlalchemy.orm import Session
from db.models import Trade

def record_trade(db: Session, trade_data: dict):
    trade = Trade(**trade_data)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade
