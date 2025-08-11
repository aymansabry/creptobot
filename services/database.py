from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Enum, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
import enum

Base = declarative_base()

class ExchangePlatform(enum.Enum):
    BINANCE = "binance"
    KUCOIN = "kucoin"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    mode = Column(Enum('live', 'demo', name='user_mode'), default='demo')
    investment_amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default='now()')

class ExchangeConnection(Base):
    __tablename__ = 'exchange_connections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    platform = Column(Enum(ExchangePlatform))
    api_key = Column(Text)
    api_secret = Column(Text)
    is_valid = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default='now()')

class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    def get_user(self, telegram_id):
        session = self.Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        session.close()
        return user
    
    def add_user(self, user_data):
        session = self.Session()
        user = User(**user_data)
        session.add(user)
        session.commit()
        session.close()
    
    def update_user(self, telegram_id, update_data):
        session = self.Session()
        session.query(User).filter_by(telegram_id=telegram_id).update(update_data)
        session.commit()
        session.close()
    
    def add_exchange_connection(self, connection_data):
        session = self.Session()
        connection = ExchangeConnection(**connection_data)
        session.add(connection)
        session.commit()
        session.close()
        return connection
    
    def get_active_connections(self, user_id):
        session = self.Session()
        connections = session.query(ExchangeConnection).filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        session.close()
        return connections
