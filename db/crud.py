from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from .models import User, UserWallet, Trade, Transaction, SystemSettings

# ======================================
# دوال المستخدمين
# ======================================
def get_user(db: Session, telegram_id: int):
    """الحصول على مستخدم بواسطة Telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int, username: str = None):
    """إنشاء مستخدم جديد"""
    db_user = User(telegram_id=telegram_id, username=username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, telegram_id: int, update_data: dict):
    """تحديث بيانات المستخدم"""
    db.query(User).filter(User.telegram_id == telegram_id).update(update_data)
    db.commit()

# ======================================
# دوال المحافظ
# ======================================
def create_wallet(db: Session, user_id: int, wallet_type: str):
    """إنشاء محفظة جديدة"""
    wallet = UserWallet(user_id=user_id, wallet_type=wallet_type)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

def get_user_wallets(db: Session, user_id: int):
    """الحصول على جميع محافظ المستخدم"""
    return db.query(UserWallet).filter(UserWallet.user_id == user_id).all()

def update_wallet_balance(db: Session, wallet_id: int, amount: float):
    """تحديث رصيد المحفظة"""
    wallet = db.query(UserWallet).filter(UserWallet.id == wallet_id).first()
    if wallet:
        wallet.balance += amount
        wallet.last_updated = datetime.now()
        db.commit()
        db.refresh(wallet)
    return wallet

# ======================================
# دوال الصفقات
# ======================================
def create_trade(db: Session, user_id: int, amount: float, trade_type: str):
    """إنشاء صفقة جديدة"""
    trade = Trade(
        user_id=user_id,
        amount=amount,
        trade_type=trade_type,
        status='pending'
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade

def update_trade_status(db: Session, trade_id: int, status: str, profit: float = None):
    """تحديث حالة الصفقة"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if trade:
        trade.status = status
        if profit is not None:
            trade.profit = profit
        trade.end_time = datetime.now()
        db.commit()
        db.refresh(trade)
    return trade

def get_active_trades(db: Session, user_id: int = None):
    """الحصول على الصفقات النشطة"""
    query = db.query(Trade).filter(Trade.status == 'active')
    if user_id:
        query = query.filter(Trade.user_id == user_id)
    return query.all()

# ======================================
# دوال المعاملات
# ======================================
def create_transaction(db: Session, wallet_id: int, amount: float, tx_type: str, tx_hash: str = None):
    """إنشاء معاملة جديدة"""
    transaction = Transaction(
        wallet_id=wallet_id,
        amount=amount,
        tx_type=tx_type,
        tx_hash=tx_hash
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def get_wallet_transactions(db: Session, wallet_id: int, limit: int = 10):
    """الحصول على سجل المعاملات للمحفظة"""
    return db.query(Transaction).filter(
        Transaction.wallet_id == wallet_id
    ).order_by(
        Transaction.timestamp.desc()
    ).limit(limit).all()

# ======================================
# دوال النظام والإحصائيات
# ======================================
def get_system_settings(db: Session):
    """الحصول على إعدادات النظام"""
    settings = db.query(SystemSettings).first()
    if not settings:
        # إنشاء إعدادات افتراضية إذا لم تكن موجودة
        settings = SystemSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def update_system_settings(db: Session, update_data: dict):
    """تحديث إعدادات النظام"""
    settings = get_system_settings(db)
    for key, value in update_data.items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings

def get_system_stats(db: Session):
    """الحصول على إحصائيات النظام"""
    now = datetime.now()
    last_24h = now - timedelta(hours=24)
    
    return {
        'total_users': db.query(func.count(User.id)).scalar(),
        'active_users': db.query(func.count(User.id)).filter(User.is_active == True).scalar(),
        'active_trades': db.query(func.count(Trade.id)).filter(Trade.status == 'active').scalar(),
        'total_profits': db.query(func.sum(Trade.profit)).scalar() or 0,
        'daily_profits': db.query(func.sum(Trade.profit)).filter(
            and_(
                Trade.status == 'completed',
                Trade.end_time >= last_24h
            )
        ).scalar() or 0,
        'total_deposits': db.query(func.sum(Transaction.amount)).filter(
            Transaction.tx_type == 'deposit'
        ).scalar() or 0
    }
