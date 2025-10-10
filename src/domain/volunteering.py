from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional
from uuid import UUID, uuid4

from .events import EventId
from .users import UserId

Role = str  # e.g., "usher", "driver", "medic"

@dataclass(frozen=True)
class OpportunityId:
    value: UUID

    @staticmethod
    def new() -> OpportunityId:
        return OpportunityId(uuid4())

@dataclass
class Opportunity:
    id: OpportunityId
    event_id: EventId
    title: str
    description: Optional[str] = None
    required_skills: list[str] = field(default_factory=list)
    min_hours: float | None = None
    max_slots: int | None = None

@dataclass(frozen=True)
class MatchRequestId:
    value: UUID

    @staticmethod
    def new() -> "MatchRequestId":
        return MatchRequestId(uuid4())

class MatchStatus(Enum):
    PENDING = auto()
    ACCEPTED = auto()
    REJECTED = auto()
    EXPIRED = auto()

@dataclass
class MatchRequest:
    id: MatchRequestId
    user_id: UserId
    opportunity_id: OpportunityId
    requested_at: datetime
    status: MatchStatus = MatchStatus.PENDING
    score: float | None = None            # optional matching score

@dataclass(frozen=True)
class MatchId:
    value: UUID

    @staticmethod
    def new() -> "MatchId":
        return MatchId(uuid4())

@dataclass
class Match:
    id: MatchId
    user_id: UserId
    opportunity_id: OpportunityId
    created_at: datetime
    status: MatchStatus
    score: float | None = None

@dataclass(frozen=True)
class VolunteerHistoryEntryId:
    value: UUID

    @staticmethod
    def new() -> "VolunteerHistoryEntryId":
        return VolunteerHistoryEntryId(uuid4())

@dataclass
class VolunteerHistoryEntry:
    id: VolunteerHistoryEntryId
    user_id: UserId
    event_id: EventId
    role: Role
    hours: float
    date: datetime
    notes: str | None = None
