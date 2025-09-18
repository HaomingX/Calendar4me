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
    
    # 新增：周期性事件字段
    is_recurring: Optional[bool] = False
    recurrence_rule: Optional[str] = Field(None, max_length=500)
    recurrence_end_date: Optional[datetime] = None

    @validator("start_time", "end_time", pre=True)
    def ensure_datetime_obj(cls, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
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

    @validator("recurrence_end_date")
    def validate_recurrence_end_date(cls, value: Optional[datetime]):
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("Recurrence end date must include timezone information")
        return value.astimezone(timezone.utc)


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
    
    # 新增：周期性事件字段
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = Field(None, max_length=500)
    recurrence_end_date: Optional[datetime] = None

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

    @validator("recurrence_end_date")
    def validate_recurrence_end_date(cls, value: Optional[datetime]):
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("Recurrence end date must include timezone information")
        return value.astimezone(timezone.utc)


class Event(EventBase):
    id: int
    reminder_sent: bool
    parent_event_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# 新增：周期性事件创建请求
class RecurringEventCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    start_time: datetime
    end_time: datetime
    reminder_minutes_before: Optional[int] = Field(None, ge=0, le=10080)
    reminder_email: Optional[EmailStr] = None
    
    # 周期性设置
    recurrence_frequency: str = Field(..., regex="^(weekly|daily|monthly)$")
    recurrence_interval: int = Field(1, ge=1, le=52)  # 间隔周数
    recurrence_end_date: datetime
    recurrence_count: Optional[int] = Field(None, ge=1, le=100)  # 重复次数（可选）

    @validator("start_time", "end_time", "recurrence_end_date")
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

    @validator("recurrence_end_date")
    def validate_recurrence_end_after_start(cls, recurrence_end_date: datetime, values):
        start_time = values.get("start_time")
        if start_time and recurrence_end_date <= start_time:
            raise ValueError("Recurrence end date must be after start time")
        return recurrence_end_date
