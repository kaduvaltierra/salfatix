from sqlalchemy.orm import relationship
from db import db
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from datetime import datetime, timezone


class User(db.Model):
   __tablename__ = "users"

   id = Column(Integer, primary_key=True, autoincrement=True)
   created_at = Column(DateTime, default=datetime.now(timezone.utc))
   email = Column(String, nullable=False, unique=True)

   messages = relationship("Message", back_populates="user")

class Message(db.Model):
   __tablename__ = "messages"
   id = Column(Integer, primary_key=True, autoincrement=True)
   created_at = Column(DateTime, default=datetime.now(timezone.utc))
   content = Column(Text, nullable=False)
   author = Column(String, nullable=False)  # 'user' or 'assistant'
   user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
   user = relationship("User", back_populates="messages")