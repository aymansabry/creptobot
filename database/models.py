from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    join_date: datetime
    balance: float = 0.0
    is_active: bool = True

@dataclass
class InvestmentOpportunity:
    id: str  # كود الفرصة
    base_currency: str
    target_currency: str
    buy_market: str
    sell_market: str
    expected_profit: float  # نسبة الربح
    duration_minutes: int
    timestamp: datetime

@dataclass
class Trade:
    trade_id: str
    user_id: int
    opportunity_id: str
    amount: float
    status: str  # pending, completed, failed
    start_time: datetime
    end_time: Optional[datetime]
    profit: Optional[float]
    commission: Optional[float]
