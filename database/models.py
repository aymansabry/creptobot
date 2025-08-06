from sqlalchemy import Column, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from config import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    wallet_address = Column(String(64))
