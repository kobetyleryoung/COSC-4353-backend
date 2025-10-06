from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from uuid import UUID, uuid4

from .users import UserId

class AuthProvider(Enum):
    PASSWORD = auto()
    GOOGLE = auto()
    GITHUB = auto()
    MICROSOFT = auto()

@dataclass
class AuthSession:
    user_id: UserId
    token: str           
    issued_at: datetime
    expires_at: datetime
    provider: AuthProvider
