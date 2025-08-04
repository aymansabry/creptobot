from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Verify table creation
Base.metadata.create_all(engine)
print("Database tables:", Base.metadata.tables.keys())

# Thread-safe session
Session = scoped_session(sessionmaker(bind=engine))

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
