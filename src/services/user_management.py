from __future__ import annotations
from typing import Optional
from logging import Logger

from src.domain.users import User, UserId, UserRole
from src.domain.repositories import UserRepository

class UserManagementService:
    """Service for managing users."""
    
    def __init__(self, logger: Logger, user_repository: UserRepository) -> None:
        self._logger = logger
        self._user_repository = user_repository
    
    def create_user(
        self,
        user_id: UserId,
        email: str,
        auth0_sub: str
    ) -> User:
        """Create a new user."""
        # Validation
        if not email or len(email.strip()) == 0:
            raise ValueError("Email is required")
        
        if not auth0_sub or len(auth0_sub.strip()) == 0:
            raise ValueError("Auth0 subject is required")
        
        # Create user with VOLUNTEER role by default
        user = User(
            id=user_id,
            email=email.strip().lower(),
            roles={UserRole.VOLUNTEER},
            auth0_sub=auth0_sub.strip()
        )
        
        self._user_repository.add(user)
        self._logger.info(f"Created user: {email} with ID {user_id.value}")
        
        return user
    
    def get_user_by_id(self, user_id: UserId) -> Optional[User]:
        """Get a user by ID."""
        return self._user_repository.get(user_id)
    
    def get_user_by_auth0_sub(self, auth0_sub: str) -> Optional[User]:
        """Get a user by Auth0 subject identifier."""
        return self._user_repository.get_by_auth0_sub(auth0_sub)
    
    def update_user(
        self,
        user_id: UserId,
        email: Optional[str] = None
    ) -> Optional[User]:
        """Update a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        if email:
            user.email = email.strip().lower()
        
        self._user_repository.save(user)
        self._logger.info(f"Updated user {user_id.value}")
        
        return user