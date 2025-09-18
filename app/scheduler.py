import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from . import crud, emailer
from .database import SessionLocal

logger = logging.getLogger(__name__)


class ReminderDispatcher:
    def __init__(self, poll_interval_seconds: int = 60) -> None:
        self.poll_interval_seconds = poll_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._smtp_settings = emailer.load_smtp_settings()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        await self._task
        self._task = None

    async def _run(self) -> None:
        logger.info("Reminder dispatcher started")
        while not self._stop_event.is_set():
            await self._dispatch_once()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.poll_interval_seconds)
            except asyncio.TimeoutError:
                continue
        logger.info("Reminder dispatcher stopped")

    async def _dispatch_once(self) -> None:
        now = datetime.now(timezone.utc)
        with SessionLocal() as db:
            due_events = crud.due_reminders(db, as_of=now, lookback_minutes=max(1, self.poll_interval_seconds // 60))
            if not due_events:
                return
            logger.debug("Processing %d due reminders", len(due_events))
            for event in due_events:
                subject = f"提醒: {event.title}"
                body_lines = [
                    f"标题: {event.title}",
                    f"开始时间 (UTC): {event.start_time.isoformat()}",
                    f"结束时间 (UTC): {event.end_time.isoformat()}",
                ]
                if event.location:
                    body_lines.append(f"地点: {event.location}")
                if event.description:
                    body_lines.append("\n备注:\n" + event.description)
                body = "\n".join(body_lines)
                try:
                    await asyncio.to_thread(
                        emailer.send_email,
                        event.reminder_email,
                        subject,
                        body,
                        self._smtp_settings,
                    )
                    crud.mark_reminder_sent(db, event)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Failed to send reminder for event %s: %s", event.id, exc)
