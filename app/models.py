from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    Text,
    Date,
    Time,
    DateTime,
    func,
    BigInteger,
    ARRAY,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): ...

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_norm: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    time: Mapped[Optional[time]] = mapped_column(Time)
    venue: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(120), default="Buenos Aires")
    genres: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String))
    support_wallet: Mapped[Optional[str]] = mapped_column(String(42))
    vibe_description: Mapped[Optional[str]] = mapped_column(Text)

    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_link: Mapped[Optional[str]] = mapped_column(Text)
    source_msg_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    media_url: Mapped[Optional[str]] = mapped_column(Text)
    dedupe_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    published_msg_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    published_topic_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CheckIn(Base):
    __tablename__ = "checkins"
    __table_args__ = (
        UniqueConstraint("event_id", "wallet_address", name="uq_checkins_event_wallet"),
        UniqueConstraint("nonce", name="uq_checkins_nonce"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), index=True, nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(42), index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
