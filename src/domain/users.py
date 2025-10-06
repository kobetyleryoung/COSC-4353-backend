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
    # Store password *hash* only if your domain really needs to reason about it
    password_hash: str | None = None
