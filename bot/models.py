from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int
    username: Optional[str]
    wallet_address: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VirtualTrade(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    crypto_symbol: str
    action: str  # "buy" or "sell"
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

