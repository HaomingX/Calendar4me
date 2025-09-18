from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional

from sqlalchemy import asc
from sqlalchemy.orm import Session

from . import models, schemas


def create_event(db: Session, event_in: schemas.EventCreate) -> models.Event:
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
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Optional[models.Event]:
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def list_events(
    db: Session,
    *,
    start_after: Optional[datetime] = None,
    end_before: Optional[datetime] = None,
    category: Optional[str] = None,
) -> List[models.Event]:
    query = db.query(models.Event).order_by(asc(models.Event.start_time))
    if start_after is not None:
        query = query.filter(models.Event.end_time >= start_after)
    if end_before is not None:
        query = query.filter(models.Event.start_time <= end_before)
    if category is not None:
        query = query.filter(models.Event.category == category)
    return query.all()


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
