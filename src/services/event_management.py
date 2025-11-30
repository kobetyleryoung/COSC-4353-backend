from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from logging import Logger

from sqlalchemy.orm import Session
from src.domain.events import Event, EventId, EventStatus, Location
from src.repositories.sqlalchemy_repositories import SqlAlchemyEventRepository


class EventManagementService:
    """Service for managing events and volunteer opportunities."""

    def __init__(self, db: Session, logger: Logger):
        self._logger: Logger = logger
        self.db: Session = db
        self.repo = SqlAlchemyEventRepository(db)

    # -----------------------------
    # CREATE EVENT
    # -----------------------------
    def create_event(
        self,
        title: str,
        description: str,
        location: Location,
        required_skills: List[str],
        starts_at: datetime,
        ends_at: Optional[datetime] = None,
        capacity: Optional[int] = None
    ) -> Event:
        # Validation
        if not title.strip():
            raise ValueError("Event title is required")
        if len(title) > 100:
            raise ValueError("Event title must be 100 characters or less")

        if not description.strip():
            raise ValueError("Event description is required")
        if len(description) > 500:
            raise ValueError("Event description must be 500 characters or less")

        if not location or not location.name:
            raise ValueError("Event location is required")

        if starts_at <= datetime.now():
            raise ValueError("Event start time must be in the future")

        if ends_at and ends_at <= starts_at:
            raise ValueError("Event end time must be after start time")

        if capacity is not None and capacity <= 0:
            raise ValueError("Event capacity must be greater than 0")

        if not required_skills:
            raise ValueError("At least one required skill must be specified")

        # Create event domain object
        event_id = EventId.new()
            
        event = Event(
            id=event_id,
            title=title.strip(),
            description=description.strip(),
            location=location,
            required_skills=required_skills,
            starts_at=starts_at,
            ends_at=ends_at,
            capacity=capacity,
            status=EventStatus.DRAFT,
        )

        # Persist to DB
        self.repo.add(event)
        self.db.commit()

        self._logger.info(f"Created new event: {title} (ID: {event_id.value})")
        return event

    # -----------------------------
    # RETRIEVAL METHODS
    # -----------------------------
    def get_event_by_id(self, event_id: EventId) -> Optional[Event]:
        return self.repo.get_by_id(event_id)

    def get_all_events(self) -> List[Event]:
        return self.repo.list_all()

    def get_published_events(self) -> List[Event]:
        return self.repo.list_by_status(EventStatus.PUBLISHED)

    def get_upcoming_events(self) -> List[Event]:
        now = datetime.now()
        return self.repo.list_upcoming(as_of=now)

    # -----------------------------
    # UPDATE METHODS
    # -----------------------------
    def update_event(
        self,
        event_id: EventId,
        title: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[Location] = None,
        required_skills: Optional[List[str]] = None,
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        capacity: Optional[int] = None,
        status: Optional[EventStatus] = None,
    ) -> Optional[Event]:
        event = self.repo.get_by_id(event_id)
        if not event:
            return None

        # Update fields
        if title:
            event.title = title.strip()
        if description:
            event.description = description.strip()
        if location:
            event.location = location
        if starts_at:
            event.starts_at = starts_at
        if ends_at:
            event.ends_at = ends_at
        if capacity:
            event.capacity = capacity
        if required_skills:
            event.required_skills = required_skills
        if status:
            event.status = status

        self.repo.update(event)
        self.db.commit()

        self._logger.info(f"Updated event: {event.title} (ID: {event_id.value})")
        return event

    def delete_event(self, event_id: EventId) -> bool:
        event = self.repo.get_by_id(event_id)
        if not event:
            return False

        self.repo.delete(event)
        self.db.commit()
        self._logger.info(f"Deleted event: {event.title} (ID: {event_id.value})")
        return True
