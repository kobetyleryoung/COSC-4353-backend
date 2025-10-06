from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from src.domain.events import Event, EventId, EventStatus, Location
from src.domain.users import UserId
from config.logging_config import logger


class EventManagementService:
    """Service for managing events and volunteer opportunities."""
    
    def __init__(self):
        # Hard-coded data storage (no database implementation)
        self._events: dict[str, Event] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self) -> None:
        """Initialize with sample events."""
        # Sample event 1: Community Cleanup
        event1_id = EventId.new()
        event1 = Event(
            id=event1_id,
            title="Community Park Cleanup",
            description="Help clean up our local park and make it beautiful for everyone",
            location=Location(
                name="Central Park",
                address="123 Park Ave",
                city="Houston",
                state="TX",
                postal_code="77001"
            ),
            required_skills=["Physical Labor", "Environmental Awareness"],
            starts_at=datetime.now() + timedelta(days=14),
            ends_at=datetime.now() + timedelta(days=14, hours=4),
            capacity=20,
            status=EventStatus.PUBLISHED
        )
        self._events[str(event1_id.value)] = event1
        
        # Sample event 2: Food Bank
        event2_id = EventId.new()
        event2 = Event(
            id=event2_id,
            title="Food Bank Distribution",
            description="Help distribute food to families in need",
            location=Location(
                name="Houston Food Bank",
                address="535 Portwall St",
                city="Houston",
                state="TX",
                postal_code="77029"
            ),
            required_skills=["Customer Service", "Physical Labor", "Organization"],
            starts_at=datetime.now() + timedelta(days=7),
            ends_at=datetime.now() + timedelta(days=7, hours=6),
            capacity=15,
            status=EventStatus.PUBLISHED
        )
        self._events[str(event2_id.value)] = event2
        
        # Sample event 3: Senior Center
        event3_id = EventId.new()
        event3 = Event(
            id=event3_id,
            title="Senior Center Activities",
            description="Assist with activities and companionship for senior residents",
            location=Location(
                name="Sunset Senior Center",
                address="123 Elder Way",
                city="Houston",
                state="TX",
                postal_code="77002"
            ),
            required_skills=["Communication", "Patience", "First Aid"],
            starts_at=datetime.now() + timedelta(days=21),
            ends_at=datetime.now() + timedelta(days=21, hours=3),
            capacity=8,
            status=EventStatus.PUBLISHED
        )
        self._events[str(event3_id.value)] = event3
        
        logger.info(f"Initialized {len(self._events)} sample events")
    
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
        event = Event(
            id=event_id,
            title=title.strip(),
            description=description.strip(),
            location=location,
            required_skills=required_skills,
            starts_at=starts_at,
            ends_at=ends_at,
            capacity=capacity,
            status=EventStatus.DRAFT
        )
        
        self._events[str(event_id.value)] = event
        logger.info(f"Created new event: {title} (ID: {event_id.value})")
        
        return event
    
    def get_event_by_id(self, event_id: EventId) -> Optional[Event]:
        """Retrieve an event by its ID."""
        return self._events.get(str(event_id.value))
    
    def get_all_events(self) -> List[Event]:
        """Retrieve all events."""
        return list(self._events.values())
    
    def get_published_events(self) -> List[Event]:
        """Retrieve all published events."""
        return [event for event in self._events.values() if event.status == EventStatus.PUBLISHED]
    
    def get_upcoming_events(self) -> List[Event]:
        """Retrieve upcoming published events."""
        now = datetime.now()
        return [
            event for event in self._events.values()
            if event.status == EventStatus.PUBLISHED and event.is_upcoming(now)
        ]
    
    def get_events_by_skills(self, skills: List[str]) -> List[Event]:
        """Retrieve events that match any of the provided skills."""
        matching_events = []
        skill_set = set(skill.lower() for skill in skills)
        
        for event in self._events.values():
            if event.status != EventStatus.PUBLISHED:
                continue
            event_skills = set(skill.lower() for skill in event.required_skills)
            if skill_set.intersection(event_skills):
                matching_events.append(event)
        
        return matching_events
    
    def get_events_by_location(self, city: str, state: str) -> List[Event]:
        """Retrieve events in a specific city and state."""
        return [
            event for event in self._events.values()
            if event.status == EventStatus.PUBLISHED
            and event.location
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
        event = self.get_event_by_id(event_id)
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
        
        logger.info(f"Updated event: {event.title} (ID: {event_id.value})")
        return event
    
    def publish_event(self, event_id: EventId) -> bool:
        """Publish an event by setting its status to PUBLISHED."""
        event = self.get_event_by_id(event_id)
        if not event:
            return False
        
        if event.status == EventStatus.CANCELLED:
            raise ValueError("Cannot publish a cancelled event")
        
        event.status = EventStatus.PUBLISHED
        logger.info(f"Published event: {event.title} (ID: {event_id.value})")
        return True
    
    def cancel_event(self, event_id: EventId) -> bool:
        """Cancel an event by setting its status to CANCELLED."""
        event = self.get_event_by_id(event_id)
        if not event:
            return False
        
        event.status = EventStatus.CANCELLED
        logger.info(f"Cancelled event: {event.title} (ID: {event_id.value})")
        return True
    
    def delete_event(self, event_id: EventId) -> bool:
        """Delete an event."""
        if str(event_id.value) not in self._events:
            return False
        
        event = self._events.pop(str(event_id.value))
        logger.info(f"Deleted event: {event.title} (ID: {event_id.value})")
        return True
    
    def get_events_with_capacity(self, enrolled_counts: dict[str, int]) -> List[Event]:
        """Get events that still have available capacity."""
        available_events = []
        
        for event in self._events.values():
            if event.status != EventStatus.PUBLISHED:
                continue
            
            enrolled = enrolled_counts.get(str(event.id.value), 0)
            if event.has_space(enrolled):
                available_events.append(event)
        
        return available_events
