from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Purchase(Base):
    __tablename__ = "purchases"
    
    session_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, primary_key=True, index=True)
    purchase_date = Column(DateTime, default=datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"
    
    session_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, primary_key=True, index=True)
    view_date = Column(DateTime, primary_key=True, index=True)
