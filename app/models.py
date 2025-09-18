from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime as SADateTime, TypeDecorator

from .database import Base


class UTCDateTime(TypeDecorator):
    """Store datetimes in UTC and restore timezone information (esp. for SQLite)."""

    impl = SADateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("Datetime must include timezone information")
        value = value.astimezone(timezone.utc)
        if dialect.name == "sqlite":
            return value.replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, str):
            # SQLite may return ISO strings from datetime columns.
            value = datetime.fromisoformat(value)
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    start_time = Column(UTCDateTime(), nullable=False)
    end_time = Column(UTCDateTime(), nullable=False)
    reminder_minutes_before = Column(Integer, nullable=True)
    reminder_email = Column(String(255), nullable=True)
    reminder_sent = Column(Boolean, nullable=False, default=False)
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    updated_at = Column(UTCDateTime(), nullable=False, server_default=func.now(), onupdate=func.now())

    def remaining_minutes_until_start(self, reference: datetime) -> int:
        delta = self.start_time - reference
        return int(delta.total_seconds() // 60)
