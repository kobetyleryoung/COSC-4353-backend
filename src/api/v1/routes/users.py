from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from uuid import UUID

from src.services.user_management import UserManagementService
from src.domain.users import UserId
from ..schemas.users import UserCreateSchema, UserResponseSchema, UserUpdateSchema
from src.config.logging_config import logger
from src.config.database_settings import get_uow

router = APIRouter(prefix="/users", tags=["users"])

def _get_user_service(uow=Depends(get_uow)) -> UserManagementService:
    return UserManagementService(logger, uow.users)

def _convert_user_to_response(user) -> UserResponseSchema:
    """Convert domain User to UserResponseSchema."""
    return UserResponseSchema(
        id=user.id.value,
        email=user.email,
        display_name=user.email.split('@')[0],  # Simple display name from email
        auth0_sub=user.auth0_sub
    )

@router.post("/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_or_get_user(
    user_data: UserCreateSchema,
    user_service: UserManagementService = Depends(_get_user_service)
):
    """Create a new user or return existing user by auth0_sub."""
    try:
        # Check if user exists by auth0_sub
        existing_user = user_service.get_user_by_auth0_sub(user_data.auth0_sub)
        if existing_user:
            logger.info(f"User already exists with auth0_sub: {user_data.auth0_sub}")
            return _convert_user_to_response(existing_user)
        
        # Create new user with deterministic UUID from auth0_sub
        from uuid import uuid5, UUID as PyUUID
        USER_NS = PyUUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        user_uuid = uuid5(USER_NS, user_data.auth0_sub)
        
        user = user_service.create_user(
            user_id=UserId(user_uuid),
            email=user_data.email,
            auth0_sub=user_data.auth0_sub
        )
        
        return _convert_user_to_response(user)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user_by_id(
    user_id: UUID,
    user_service: UserManagementService = Depends(_get_user_service)
):
    """Get a user by ID."""
    try:
        user = user_service.get_user_by_id(UserId(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return _convert_user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@router.get("/by-auth0/{auth0_sub}", response_model=UserResponseSchema)
async def get_user_by_auth0_sub(
    auth0_sub: str,
    user_service: UserManagementService = Depends(_get_user_service)
):
    """Get a user by Auth0 subject identifier."""
    try:
        user = user_service.get_user_by_auth0_sub(auth0_sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return _convert_user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by auth0_sub {auth0_sub}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )