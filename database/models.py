from sqlalchemy import Column, String, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from database.encryption import CryptoManager
from config import config

Base = declarative_base()
crypto = CryptoManager(config.ENCRYPTION_KEY)

class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    encrypted_wallet = Column(String)
    
    @property
    def wallet(self):
        return crypto.decrypt(self.encrypted_wallet)
    
    @wallet.setter
    def wallet(self, value):
        self.encrypted_wallet = crypto.encrypt(value)
