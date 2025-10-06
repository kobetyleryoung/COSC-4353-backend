from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional
from uuid import UUID, uuid4

from .users import UserId

Skill = str  # keep lightweight; refine later if needed

@dataclass(frozen=True)
class AvailabilityWindow:
    weekday: int           # 0=Mon ... 6=Sun
    start: time
    end: time

@dataclass
class Profile:
    user_id: UserId
    display_name: Optional[str] = None
    phone: Optional[str] = None
    skills: list[Skill] = field(default_factory=list)
    # free-form tags like "spanish", "first aid", "driver"
    tags: list[str] = field(default_factory=list)
    availability: list[AvailabilityWindow] = field(default_factory=list)
    updated_at: datetime | None = None
