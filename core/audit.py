from datetime import datetime
from database import get_db
from sqlalchemy import Column, DateTime, String, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(String, primary_key=True)
    action = Column(String)
    amount = Column(Numeric)
    timestamp = Column(DateTime, default=datetime.utcnow)
