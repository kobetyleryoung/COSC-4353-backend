# domain/users.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Set
from uuid import UUID, uuid4

@dataclass(frozen=True)
class UserId:
    value: UUID

    @staticmethod
    def new() -> "UserId":
        return UserId(uuid4())

class UserRole(Enum):
    ADMIN = auto()
    ORGANIZER = auto()
    VOLUNTEER = auto()

@dataclass
class User:
    id: UserId
    email: str
    roles: Set[UserRole] = field(default_factory=set)
    # Auth0 subject identifier for linking to Auth0 user
    auth0_sub: str | None = None
