from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import BigInteger, String, DateTime, Text, ForeignKey, Integer, Date
from datetime import datetime
from typing import List
from dotenv import load_dotenv
import os
load_dotenv()
engine = create_async_engine(url=os.getenv("URL_BD"), echo=True, future=True)

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users_bot"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связь с выбранными местами
    selected_spots: Mapped[List["SelectedFishingSpot"]] = relationship(
        "SelectedFishingSpot", 
        back_populates="user",
        cascade="all, delete-orphan"
    )

class SelectedFishingSpot(Base):
    __tablename__ = "selected_fishing_spots"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users_bot.id"), nullable=False)
    

    spot_name: Mapped[str] = mapped_column(String(255), nullable=False)
    spot_coordinates: Mapped[str] = mapped_column(String(100), nullable=True)  # "lat,lon"
    fishing_date: Mapped[Date] = mapped_column(Date, nullable=False)
    # Контекст поиска
    user_query: Mapped[str] = mapped_column(Text, nullable=True)  # Оригинальный запрос пользователя
    user_coordinates: Mapped[str] = mapped_column(String(100), nullable=True)  # Координаты пользователя
    
    # Метаданные
    selected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="selected_spots")

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(async_main())
    print("✔️ Все таблицы успешно созданы")