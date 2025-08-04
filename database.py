from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    user_id = Column(Integer)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Conversation(chat_id={self.chat_id}, user_id={self.user_id}, message='{self.message}')>"

def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

# Initialize database
engine = init_db()
Session = get_session(engine)
