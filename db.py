from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from cryptography.fernet import Fernet
import datetime
import os

Base = declarative_base()

# تشفير بيانات API
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = Fernet.generate_key().decode()
    print(f"⚠️ لم يتم العثور على SECRET_KEY، تم إنشاء مفتاح جديد: {SECRET_KEY}")

fernet = Fernet(SECRET_KEY.encode())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    profit = Column(Float, default=0.0)
    binance_api_key = Column(String)
    binance_api_secret = Column(String)
    kucoin_api_key = Column(String)
    kucoin_api_secret = Column(String)
    kucoin_api_passphrase = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def set_binance_keys(self, api_key, api_secret):
        self.binance_api_key = fernet.encrypt(api_key.encode()).decode()
        self.binance_api_secret = fernet.encrypt(api_secret.encode()).decode()

    def get_binance_keys(self):
        if self.binance_api_key and self.binance_api_secret:
            return (
                fernet.decrypt(self.binance_api_key.encode()).decode(),
                fernet.decrypt(self.binance_api_secret.encode()).decode()
            )
        return None, None

    def set_kucoin_keys(self, api_key, api_secret, passphrase):
        self.kucoin_api_key = fernet.encrypt(api_key.encode()).decode()
        self.kucoin_api_secret = fernet.encrypt(api_secret.encode()).decode()
        self.kucoin_api_passphrase = fernet.encrypt(passphrase.encode()).decode()

    def get_kucoin_keys(self):
        if self.kucoin_api_key and self.kucoin_api_secret and self.kucoin_api_passphrase:
            return (
                fernet.decrypt(self.kucoin_api_key.encode()).decode(),
                fernet.decrypt(self.kucoin_api_secret.encode()).decode(),
                fernet.decrypt(self.kucoin_api_passphrase.encode()).decode()
            )
        return None, None, None


DB_URL = "sqlite:///bot.db"
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("✅ قاعدة البيانات جاهزة")

def get_session():
    return SessionLocal()
