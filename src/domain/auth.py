"""
Auth0 integration utilities for the volunteer management system.

Since authentication is handled by Auth0, this module provides
utilities for working with Auth0 user data and tokens.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

from .users import UserId

@dataclass
class Auth0User:
    """
    Auth0 user information extracted from JWT tokens.
    
    This represents the user data we get from Auth0 after
    successful authentication.
    """
    sub: str  # Auth0 subject identifier (unique user ID)
    email: str
    email_verified: bool = False
    name: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    
    @classmethod
    def from_auth0_payload(cls, payload: Dict[str, Any]) -> "Auth0User":
        """Create Auth0User from JWT payload."""
        return cls(
            sub=payload["sub"],
            email=payload["email"],
            email_verified=payload.get("email_verified", False),
            name=payload.get("name"),
            picture=payload.get("picture"),
            given_name=payload.get("given_name"),
            family_name=payload.get("family_name")
        )
