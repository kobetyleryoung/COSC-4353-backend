"""
FastAPI dependencies for user management.

For homework/development purposes, we trust the userId from the request.
In production, this would validate JWT tokens from Auth0.
"""
from fastapi import Depends, HTTPException, status
from uuid import UUID

from src.repositories.database import get_uow
from src.repositories.unit_of_work import UnitOfWorkManager
from src.domain.users import User, UserId
from src.config.logging_config import logger


async def get_or_create_user(
    user_id: str,
    uow = Depends(get_uow),
) -> User:
    """
    Get or create a user from the database by user_id.
    
    For homework purposes, we trust the user_id provided by the frontend.
    The user_id IS the UUID that will be used as the primary key.
    
    Args:
        user_id: The user ID (UUID string from Auth0 or frontend)
        uow: Unit of work for database operations
        
    Returns:
        The User domain object
    """
    try:
        # Parse the user_id as UUID
        user_uuid = UUID(user_id)
        user_id_obj = UserId(user_uuid)
        
        # Try to find existing user by ID first
        user = uow.users.get(user_id_obj)
        
        # If not found by ID, try by auth0_sub (for backwards compatibility)
        if user is None:
            user = uow.users.get_by_auth0_sub(user_id)
        
        if user is None:
            # Create new user with the provided UUID as the ID
            logger.info(f"Creating new user with ID: {user_id}")
            
            user = User(
                id=user_id_obj,  # Use the provided UUID
                email=f"user-{user_id}@example.com",  # Unique placeholder email
                auth0_sub=user_id,  # Store Auth0 sub for reference
            )
            
            # Save the new user
            uow.users.add(user)
            # Note: commit is handled by the get_uow dependency
            
            # Refresh to get the saved user
            user = uow.users.get(user_id_obj)
        else:
            # If user exists but has different ID than expected, update to use consistent ID
            if user.id.value != user_uuid:
                logger.info(f"Found user by auth0_sub but ID mismatch. Updating to use ID: {user_id}")
                # For simplicity, just use the existing user
                # In production, you might want to migrate the data
            
        return user
            
    except ValueError as e:
        logger.error(f"Invalid user_id format: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error getting/creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve user information",
        )
