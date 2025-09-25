from __future__ import annotations
from sqlalchemy import create_engine, String, Integer, Enum as SAEnum, ForeignKey, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy.sql import func
import uuid
from typing import Optional
from models import Channel


class Base(DeclarativeBase):
    pass


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text())
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    delivered_via: Mapped[Optional[Channel]] = mapped_column(SAEnum(Channel), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    attempts: Mapped[list[DeliveryAttempt]] = relationship(back_populates="notification", cascade="all, delete-orphan")


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_id: Mapped[str] = mapped_column(String(36), ForeignKey("notifications.id"), index=True)
    channel: Mapped[Channel] = mapped_column(SAEnum(Channel))
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    success: Mapped[bool] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    notification: Mapped[Notification] = relationship(back_populates="attempts")


_engine = None


def init_engine(database_url: str):
    global _engine
    if _engine is None:
        _engine = create_engine(database_url, echo=False, future=True)
        Base.metadata.create_all(_engine)
    return _engine


def get_session() -> Session:
    if _engine is None:
        raise RuntimeError("Engine is not initialized. Call init_engine() first.")
    return Session(_engine)
