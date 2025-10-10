from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional
from uuid import UUID, uuid4

from .users import UserId

@dataclass(frozen=True)
class NotificationId:
    value: UUID

    @staticmethod
    def new() -> NotificationId:
        return NotificationId(uuid4())

class NotificationChannel(Enum):
    EMAIL = auto()
    SMS = auto()
    PUSH = auto()
    IN_APP = auto()

class NotificationStatus(Enum):
    QUEUED = auto()
    SENT = auto()
    FAILED = auto()

@dataclass
class Notification:
    id: NotificationId
    recipient: UserId
    subject: str
    body: str
    channel: NotificationChannel
    status: NotificationStatus = NotificationStatus.QUEUED
    queued_at: datetime | None = None
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
