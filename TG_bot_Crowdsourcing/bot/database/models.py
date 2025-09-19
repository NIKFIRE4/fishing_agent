"""
Модели базы данных SQLAlchemy
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)  # Telegram user ID
    username = Column(String, nullable=True)  # Telegram username
    first_name = Column(String, nullable=True)  # Имя пользователя
    last_name = Column(String, nullable=True)  # Фамилия пользователя
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    posts_count = Column(Integer, default=0)  # Количество опубликованных постов
    submitted_posts_count = Column(Integer, default=0)  # Количество отправленных на модерацию постов
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', posts={self.posts_count})>"