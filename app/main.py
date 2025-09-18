import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Generator, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import Base, SessionLocal, engine
from .scheduler import ReminderDispatcher

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("itinerary_app")

poll_interval = int(os.getenv("REMINDER_POLL_INTERVAL", "60"))
dispatcher = ReminderDispatcher(poll_interval_seconds=poll_interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    await dispatcher.start()
    try:
        yield
    finally:
        await dispatcher.stop()


app = FastAPI(title="Itinerary Planner", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/events", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_in: schemas.EventCreate,
    db: Session = Depends(get_db_session),
):
    try:
        event = crud.create_event(db, event_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return event


@app.get("/events", response_model=list[schemas.Event])
async def list_events(
    start_after: Optional[datetime] = None,
    end_before: Optional[datetime] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    events = crud.list_events(db, start_after=start_after, end_before=end_before, category=category)
    return events


@app.get("/events/{event_id}", response_model=schemas.Event)
async def read_event(event_id: int, db: Session = Depends(get_db_session)):
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@app.patch("/events/{event_id}", response_model=schemas.Event)
async def update_event(
    event_id: int,
    event_in: schemas.EventUpdate,
    db: Session = Depends(get_db_session),
):
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    try:
        updated = crud.update_event(db, event=event, event_in=event_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return updated


@app.delete("/events/by-category", response_model=dict)
async def delete_events_by_category(
    category: str = Query(..., min_length=1, max_length=50),
    db: Session = Depends(get_db_session),
):
    deleted = crud.delete_events_by_category(db, category=category)
    return {"deleted": deleted}


@app.delete("/events/by-title", response_model=dict)
async def delete_events_by_title(
    title: str = Query(..., min_length=1, max_length=255),
    db: Session = Depends(get_db_session),
):
    deleted = crud.delete_events_by_title(db, title=title)
    return {"deleted": deleted}


@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: Session = Depends(get_db_session)):
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    crud.delete_event(db, event=event)
    return None
