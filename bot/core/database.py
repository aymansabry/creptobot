from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from ..config import settings

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50))
    username = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class Database:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        return self.Session()

# Initialize on import
db = Database()
db.init_db()
