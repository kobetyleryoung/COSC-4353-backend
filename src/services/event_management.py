from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from logging import Logger

from src.domain.events import Event, EventId, EventStatus, Location
from src.domain.users import UserId
from src.repositories.unit_of_work import UnitOfWorkManager


class EventManagementService:
    """Service for managing events and volunteer opportunities."""
    
    def __init__(self, uow_manager: UnitOfWorkManager, logger: Logger):
        self._uow_manager = uow_manager
        self._logger = logger
    
    def create_event(
        self,
        title: str,
        description: str,
        location: Location,
        required_skills: List[str],
        starts_at: datetime,
        ends_at: Optional[datetime] = None,
        capacity: Optional[int] = None,
        organizer_id: Optional[UserId] = None
    ) -> Event:
        """Create a new event."""
        # Validation
        if not title or len(title.strip()) == 0:
            raise ValueError("Event title is required")
        if len(title) > 100:
            raise ValueError("Event title must be 100 characters or less")
        
        if not description or len(description.strip()) == 0:
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
        
        if not required_skills or len(required_skills) == 0:
            raise ValueError("At least one required skill must be specified")
        
        # Create event
        event_id = EventId.new()
        
        # If no organizer_id provided, create a default one (in real app, get from auth context)
        if not organizer_id:
            organizer_id = UserId.new()
            
        event = Event(
            id=event_id,
            title=title.strip(),
            description=description.strip(),
            location=location,
            required_skills=required_skills,
            organizer_id=organizer_id,
            starts_at=starts_at,
            ends_at=ends_at,
            capacity=capacity,
            status=EventStatus.DRAFT
        )
        
        with self._uow_manager.get_uow() as uow:
            uow.events.add(event)
            uow.commit()
        
        self._logger.info(f"Created new event: {title} (ID: {event_id.value})")
        return event
    
    def get_event_by_id(self, event_id: EventId) -> Optional[Event]:
        """Retrieve an event by its ID."""
        with self._uow_manager.get_uow() as uow:
            return uow.events.get_by_id(event_id)
    
    def get_all_events(self) -> List[Event]:
        """Retrieve all events."""
        with self._uow_manager.get_uow() as uow:
            return uow.events.list_all()
    
    def get_published_events(self) -> List[Event]:
        """Retrieve all published events."""
        with self._uow_manager.get_uow() as uow:
            return uow.events.get_by_status(EventStatus.PUBLISHED)
    
    def get_upcoming_events(self) -> List[Event]:
        """Retrieve upcoming published events."""
        now = datetime.now()
        with self._uow_manager.get_uow() as uow:
            all_events = uow.events.get_by_status(EventStatus.PUBLISHED)
            return [event for event in all_events if event.is_upcoming(now)]
    
    def get_events_by_skills(self, skills: List[str]) -> List[Event]:
        """Retrieve events that match any of the provided skills."""
        with self._uow_manager.get_uow() as uow:
            return uow.events.get_by_skills(skills)
    
    def get_events_by_location(self, city: str, state: str) -> List[Event]:
        """Retrieve events in a specific city and state."""
        with self._uow_manager.get_uow() as uow:
            all_events = uow.events.get_by_status(EventStatus.PUBLISHED)
            return [
                event for event in all_events
                if event.location
                and event.location.city and event.location.city.lower() == city.lower()
                and event.location.state and event.location.state.lower() == state.lower()
            ]
    
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
        status: Optional[EventStatus] = None
    ) -> Optional[Event]:
        """Update an existing event."""
        with self._uow_manager.get_uow() as uow:
            event = uow.events.get_by_id(event_id)
            if not event:
                return None
            
            # Validation for updates
            if title is not None:
                if not title or len(title.strip()) == 0:
                    raise ValueError("Event title cannot be empty")
                if len(title) > 100:
                    raise ValueError("Event title must be 100 characters or less")
                event.title = title.strip()
            
            if description is not None:
                if not description or len(description.strip()) == 0:
                    raise ValueError("Event description cannot be empty")
                if len(description) > 500:
                    raise ValueError("Event description must be 500 characters or less")
                event.description = description.strip()
            
            if location is not None:
                if not location.name:
                    raise ValueError("Location name cannot be empty")
                event.location = location
            
            if starts_at is not None:
                if starts_at <= datetime.now():
                    raise ValueError("Event start time must be in the future")
                event.starts_at = starts_at
            
            if ends_at is not None:
                if ends_at <= event.starts_at:
                    raise ValueError("Event end time must be after start time")
                event.ends_at = ends_at
            
            if capacity is not None:
                if capacity <= 0:
                    raise ValueError("Event capacity must be greater than 0")
                event.capacity = capacity
            
            if required_skills is not None:
                if not required_skills or len(required_skills) == 0:
                    raise ValueError("At least one required skill must be specified")
                event.required_skills = required_skills
            
            if status is not None:
                event.status = status
            
            uow.events.update(event)
            uow.commit()
            
            self._logger.info(f"Updated event: {event.title} (ID: {event_id.value})")
            return event
    
    def publish_event(self, event_id: EventId) -> bool:
        """Publish an event by setting its status to PUBLISHED."""
        with self._uow_manager.get_uow() as uow:
            event = uow.events.get_by_id(event_id)
            if not event:
                return False
            
            if event.status == EventStatus.CANCELLED:
                raise ValueError("Cannot publish a cancelled event")
            
            event.status = EventStatus.PUBLISHED
            uow.events.update(event)
            uow.commit()
            
            self._logger.info(f"Published event: {event.title} (ID: {event_id.value})")
            return True
    
    def cancel_event(self, event_id: EventId) -> bool:
        """Cancel an event by setting its status to CANCELLED."""
        with self._uow_manager.get_uow() as uow:
            event = uow.events.get_by_id(event_id)
            if not event:
                return False
            
            event.status = EventStatus.CANCELLED
            uow.events.update(event)
            uow.commit()
            
            self._logger.info(f"Cancelled event: {event.title} (ID: {event_id.value})")
            return True
    
    def delete_event(self, event_id: EventId) -> bool:
        """Delete an event."""
        with self._uow_manager.get_uow() as uow:
            event = uow.events.get_by_id(event_id)
            if not event:
                return False
            
            uow.events.delete(event_id)
            uow.commit()
            
            self._logger.info(f"Deleted event: {event.title} (ID: {event_id.value})")
            return True
    
    def get_events_with_capacity(self, enrolled_counts: dict[str, int]) -> List[Event]:
        """Get events that still have available capacity."""
        with self._uow_manager.get_uow() as uow:
            published_events = uow.events.get_by_status(EventStatus.PUBLISHED)
            
        available_events = []
        for event in published_events:
            enrolled = enrolled_counts.get(str(event.id.value), 0)
            if event.has_space(enrolled):
                available_events.append(event)
        
        return available_events
