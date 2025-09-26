from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional

from sqlalchemy import asc
from sqlalchemy.orm import Session

from . import models, schemas
from .utils import (
    generate_recurrence_dates,
    create_rrule_string,
    parse_ical_rrule,
    get_week_number,
)


def create_event(db: Session, event_in: schemas.EventCreate) -> models.Event:
    """创建单个事件"""
    if event_in.reminder_minutes_before is not None and event_in.reminder_email is None:
        raise ValueError("Reminder email must be supplied when setting reminder minutes")
    if event_in.reminder_email is not None and event_in.reminder_minutes_before is None:
        raise ValueError("Reminder minutes must be supplied when reminder email is set")

    event = models.Event(
        title=event_in.title,
        description=event_in.description,
        category=event_in.category,
        location=event_in.location,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
        reminder_minutes_before=event_in.reminder_minutes_before,
        reminder_email=event_in.reminder_email,
        reminder_sent=False,
        is_recurring=event_in.is_recurring or False,
        recurrence_rule=event_in.recurrence_rule,
        recurrence_end_date=event_in.recurrence_end_date,
        parent_event_id=None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_recurring_event(db: Session, event_in: schemas.RecurringEventCreate) -> List[models.Event]:
    """创建周期性事件"""
    if event_in.reminder_minutes_before is not None and event_in.reminder_email is None:
        raise ValueError("Reminder email must be supplied when setting reminder minutes")
    if event_in.reminder_email is not None and event_in.reminder_minutes_before is None:
        raise ValueError("Reminder minutes must be supplied when reminder email is set")

    # 生成重复日期
    recurrence_dates = generate_recurrence_dates(
        start_date=event_in.start_time,
        end_date=event_in.end_time,
        frequency=event_in.recurrence_frequency,
        interval=event_in.recurrence_interval,
        until_date=event_in.recurrence_end_date,
        count=event_in.recurrence_count
    )

    # 创建RRULE字符串
    rrule = create_rrule_string(
        frequency=event_in.recurrence_frequency,
        interval=event_in.recurrence_interval,
        until_date=event_in.recurrence_end_date,
        count=event_in.recurrence_count
    )

    events = []
    parent_event = None

    for i, (start_time, end_time) in enumerate(recurrence_dates):
        event = models.Event(
            title=event_in.title,
            description=event_in.description,
            category=event_in.category,
            location=event_in.location,
            start_time=start_time,
            end_time=end_time,
            reminder_minutes_before=event_in.reminder_minutes_before,
            reminder_email=event_in.reminder_email,
            reminder_sent=False,
            is_recurring=True,
            recurrence_rule=rrule if i == 0 else None,  # 只在第一个事件中存储RRULE
            recurrence_end_date=event_in.recurrence_end_date,
            parent_event_id=None if i == 0 else (parent_event.id if parent_event else None),
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        if i == 0:
            parent_event = event
            # 更新父事件的parent_event_id为自己
            parent_event.parent_event_id = parent_event.id
            db.commit()
            db.refresh(parent_event)
        
        events.append(event)

    return events


def create_recurring_event_from_ical(db: Session, ical_data: dict) -> List[models.Event]:
    """从iCal数据创建周期性事件"""
    # 解析RRULE
    rrule_data = parse_ical_rrule(ical_data.get('RRULE', ''))
    
    # 解析时间
    start_time_str = ical_data.get('DTSTART', '').replace('TZID=Asia/Shanghai:', '')
    end_time_str = ical_data.get('DTEND', '').replace('TZID=Asia/Shanghai:', '')
    
    if not start_time_str or not end_time_str:
        raise ValueError("Invalid iCal time format")
    
    start_time = datetime.strptime(start_time_str, '%Y%m%dT%H%M%S')
    start_time = start_time.replace(tzinfo=timezone(timedelta(hours=8)))  # 北京时间
    start_time = start_time.astimezone(timezone.utc)
    
    end_time = datetime.strptime(end_time_str, '%Y%m%dT%H%M%S')
    end_time = end_time.replace(tzinfo=timezone(timedelta(hours=8)))  # 北京时间
    end_time = end_time.astimezone(timezone.utc)
    
    # 创建周期性事件
    recurring_event = schemas.RecurringEventCreate(
        title=ical_data.get('SUMMARY', ''),
        description=ical_data.get('DESCRIPTION', ''),
        category='course',
        location=ical_data.get('LOCATION', ''),
        start_time=start_time,
        end_time=end_time,
        reminder_minutes_before=20,  # 默认20分钟提醒
        recurrence_frequency=rrule_data.get('frequency', 'weekly'),
        recurrence_interval=rrule_data.get('interval', 1),
        recurrence_end_date=rrule_data.get('until_date'),
    )
    
    return create_recurring_event(db, recurring_event)


def get_event(db: Session, event_id: int) -> Optional[models.Event]:
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def list_events(
    db: Session,
    *,
    start_after: Optional[datetime] = None,
    end_before: Optional[datetime] = None,
    category: Optional[str] = None,
    include_recurring: bool = True,
) -> List[models.Event]:
    query = db.query(models.Event).order_by(asc(models.Event.start_time))
    
    if start_after is not None:
        query = query.filter(models.Event.end_time >= start_after)
    if end_before is not None:
        query = query.filter(models.Event.start_time <= end_before)
    if category is not None:
        query = query.filter(models.Event.category == category)
    if not include_recurring:
        query = query.filter(models.Event.is_recurring == False)
    
    return query.all()


def list_recurring_events(db: Session) -> List[models.Event]:
    """获取所有周期性事件（只返回父事件）"""
    return (
        db.query(models.Event)
        .filter(models.Event.is_recurring == True)
        .filter(models.Event.parent_event_id == models.Event.id)  # 只返回父事件
        .order_by(asc(models.Event.start_time))
        .all()
    )


def get_recurring_event_instances(db: Session, parent_event_id: int) -> List[models.Event]:
    """获取周期性事件的所有实例"""
    return (
        db.query(models.Event)
        .filter(
            (models.Event.parent_event_id == parent_event_id) |
            (models.Event.id == parent_event_id)
        )
        .order_by(asc(models.Event.start_time))
        .all()
    )


def update_event(
    db: Session,
    *,
    event: models.Event,
    event_in: schemas.EventUpdate,
) -> models.Event:
    data = event_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(event, field, value)

    if event.end_time <= event.start_time:
        raise ValueError("End time must be after start time")

    if event.reminder_email is None:
        event.reminder_minutes_before = None
        event.reminder_sent = False
    else:
        if event.reminder_minutes_before is None:
            raise ValueError("Reminder minutes must be supplied when reminder email is set")
        event.reminder_sent = False

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, *, event: models.Event) -> None:
    """删除事件"""
    if event.is_recurring and event.parent_event_id == event.id:
        # 删除整个周期性事件系列
        instances = get_recurring_event_instances(db, event.id)
        for instance in instances:
            db.delete(instance)
    else:
        db.delete(event)
    db.commit()


def delete_events_by_category(db: Session, category: str) -> int:
    deleted = db.query(models.Event).filter(models.Event.category == category).delete(synchronize_session=False)
    db.commit()
    return deleted


def delete_events_by_title(db: Session, title: str) -> int:
    deleted = db.query(models.Event).filter(models.Event.title == title).delete(synchronize_session=False)
    db.commit()
    return deleted


def due_reminders(db: Session, *, as_of: datetime, lookback_minutes: int = 5) -> Iterable[models.Event]:
    if as_of.tzinfo is None or as_of.tzinfo.utcoffset(as_of) is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    candidates = (
        db.query(models.Event)
        .filter(models.Event.reminder_sent.is_(False))
        .filter(models.Event.reminder_email.is_not(None))
        .filter(models.Event.reminder_minutes_before.is_not(None))
        .filter(models.Event.start_time >= as_of - timedelta(days=7))
        .order_by(asc(models.Event.start_time))
        .all()
    )
    due: List[models.Event] = []
    for event in candidates:
        reminder_time = event.start_time - timedelta(minutes=event.reminder_minutes_before)
        if reminder_time <= as_of and reminder_time >= as_of - timedelta(minutes=lookback_minutes):
            due.append(event)
    return due


def mark_reminder_sent(db: Session, event: models.Event) -> None:
    event.reminder_sent = True
    db.add(event)
    db.commit()
