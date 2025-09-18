from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class EventBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    start_time: datetime
    end_time: datetime
    reminder_minutes_before: Optional[int] = Field(None, ge=0, le=10080)
    reminder_email: Optional[EmailStr] = None

    @validator("start_time", "end_time", pre=True)
    def ensure_datetime_obj(cls, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Defer to Pydantic's parsing by returning the string untouched.
            return value
        raise ValueError("Datetime value must be datetime or ISO format string")

    @validator("start_time", "end_time")
    def ensure_timezone(cls, value: datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("Datetime must include timezone information")
        return value.astimezone(timezone.utc)

    @validator("end_time")
    def validate_end_after_start(cls, end_time: datetime, values):
        start_time = values.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("End time must be after start time")
        return end_time


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reminder_minutes_before: Optional[int] = Field(None, ge=0, le=10080)
    reminder_email: Optional[EmailStr] = None

    @validator("start_time", "end_time", pre=True)
    def ensure_datetime_obj(cls, value):
        if value is None:
            return value
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return value
        raise ValueError("Datetime value must be datetime or ISO format string")

    @validator("start_time", "end_time")
    def ensure_timezone(cls, value: Optional[datetime]):
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("Datetime must include timezone information")
        return value.astimezone(timezone.utc)

    @validator("end_time")
    def validate_end_after_start(cls, end_time: Optional[datetime], values):
        start_time = values.get("start_time")
        if start_time and end_time and end_time <= start_time:
            raise ValueError("End time must be after start time")
        return end_time


class Event(EventBase):
    id: int
    reminder_sent: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
