from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional
from uuid import UUID, uuid4

@dataclass(frozen=True)
class EventId:
    value: UUID

    @staticmethod
    def new() -> EventId:
        return EventId(uuid4())

@dataclass
class Location:
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

class EventStatus(Enum):
    DRAFT = auto()
    PUBLISHED = auto()
    CANCELLED = auto()

@dataclass
class Event:
    id: EventId
    title: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    location: Optional[Location] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    status: EventStatus = EventStatus.DRAFT
    required_skills: list[str] = field(default_factory=list)

    def is_upcoming(self, now: datetime) -> bool:
        return self.starts_at >= now

    def has_space(self, enrolled: int) -> bool:
        return self.capacity is None or enrolled < self.capacity
