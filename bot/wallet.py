ifrom typing import Optional
from .models import User
from sqlmodel import Session, select
from .db import engine

def get_user_wallet(user_id: int) -> Optional[str]:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.telegram_id == user_id)).first()
        return user.wallet_address if user else None

def create_virtual_wallet(user_id: int, address: str) -> None:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.telegram_id == user_id)).first()
        if user:
            user.wallet_address = address
            session.add(user)
            session.commit()
        else:
            user = User(telegram_id=user_id, wallet_address=address)
            session.add(user)
            session.commit()
