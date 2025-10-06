from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID
from functools import lru_cache

from src.services.profile_management import ProfileManagementService
from src.services.volunteer_history import VolunteerHistoryService
from src.domain.users import UserId
from src.domain.profiles import AvailabilityWindow
from ..schemas.profile import (
    ProfileCreateSchema, ProfileUpdateSchema, ProfileResponseSchema,
    AddSkillSchema, AddTagSchema, AvailabilityWindowSchema, ProfileStatsSchema
)
from config.logging_config import logger

# profiles sub url definition
router = APIRouter(prefix="/profiles", tags=["profiles"])

#region helpers

#TODO: remove lru_cache once we hookup to database
#lru_cache creates this as a singleton instead of per_request
# we use the singleton for now since we have no database, just
# test data we store in memory. Once we hookup to db we will go with
# per instance
@lru_cache(maxsize=1) 
def _get_profile_service() -> ProfileManagementService:
    return ProfileManagementService()

#TODO: see above todo
@lru_cache(maxsize=1) 
def _get_history_service() -> VolunteerHistoryService:
    return VolunteerHistoryService()


def _convert_availability_schema_to_domain(availability_schema: AvailabilityWindowSchema) -> AvailabilityWindow:
    """Convert AvailabilityWindowSchema to domain AvailabilityWindow."""
    return AvailabilityWindow(
        weekday=availability_schema.weekday,
        start=availability_schema.start,
        end=availability_schema.end
    )


def _convert_availability_domain_to_schema(availability: AvailabilityWindow) -> AvailabilityWindowSchema:
    """Convert domain AvailabilityWindow to AvailabilityWindowSchema."""
    return AvailabilityWindowSchema(
        weekday=availability.weekday,
        start=availability.start,
        end=availability.end
    )


def _convert_profile_to_response(profile) -> ProfileResponseSchema:
    """Convert domain Profile to ProfileResponseSchema."""
    availability_schemas = [
        _convert_availability_domain_to_schema(window)
        for window in profile.availability
    ]
    
    return ProfileResponseSchema(
        user_id=profile.user_id.value,
        display_name=profile.display_name,
        phone=profile.phone,
        skills=profile.skills,
        tags=profile.tags,
        availability=availability_schemas,
        updated_at=profile.updated_at
    )

#endregion

#region routes
@router.get("/", response_model=List[ProfileResponseSchema])
async def get_all_profiles(
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Get all user profiles."""
    try:
        profiles = profile_service.get_all_profiles()
        return [_convert_profile_to_response(profile) for profile in profiles]
    except Exception as e:
        logger.error(f"Error getting all profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profiles"
        )


@router.get("/{user_id}", response_model=ProfileResponseSchema)
async def get_profile_by_user_id(
    user_id: UUID,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Get a user's profile by user ID."""
    try:
        profile = profile_service.get_profile_by_user_id(UserId(user_id))
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return _convert_profile_to_response(profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.post("/", response_model=ProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreateSchema,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Create a new user profile."""
    try:
        # Convert availability windows
        availability_windows = [
            _convert_availability_schema_to_domain(window)
            for window in profile_data.availability
        ]
        
        # In real app, get user_id from authenticated user
        user_id = UserId.new()
        
        profile = profile_service.create_profile(
            user_id=user_id,
            display_name=profile_data.display_name,
            phone=profile_data.phone,
            skills=profile_data.skills,
            tags=profile_data.tags,
            availability=availability_windows
        )
        
        return _convert_profile_to_response(profile)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile"
        )


@router.put("/{user_id}", response_model=ProfileResponseSchema)
async def update_profile(
    user_id: UUID,
    profile_data: ProfileUpdateSchema,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Update an existing user profile."""
    try:
        # Convert availability windows if provided
        availability_windows = None
        if profile_data.availability is not None:
            availability_windows = [
                _convert_availability_schema_to_domain(window)
                for window in profile_data.availability
            ]
        
        profile = profile_service.update_profile(
            user_id=UserId(user_id),
            display_name=profile_data.display_name,
            phone=profile_data.phone,
            skills=profile_data.skills,
            tags=profile_data.tags,
            availability=availability_windows
        )
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return _convert_profile_to_response(profile)
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error updating profile for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/{user_id}/skills")
async def add_skill(
    user_id: UUID,
    skill_data: AddSkillSchema,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Add a skill to a user's profile."""
    try:
        success = profile_service.add_skill(UserId(user_id), skill_data.skill)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return {"message": f"Skill '{skill_data.skill}' added successfully"}
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error adding skill to user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add skill"
        )


@router.delete("/{user_id}/skills/{skill}")
async def remove_skill(
    user_id: UUID,
    skill: str,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Remove a skill from a user's profile."""
    try:
        success = profile_service.remove_skill(UserId(user_id), skill)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile or skill not found"
            )
        
        return {"message": f"Skill '{skill}' removed successfully"}
    except Exception as e:
        logger.error(f"Error removing skill from user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove skill"
        )


@router.post("/{user_id}/tags")
async def add_tag(
    user_id: UUID,
    tag_data: AddTagSchema,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Add a tag to a user's profile."""
    try:
        success = profile_service.add_tag(UserId(user_id), tag_data.tag)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return {"message": f"Tag '{tag_data.tag}' added successfully"}
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error adding tag to user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add tag"
        )


@router.delete("/{user_id}/tags/{tag}")
async def remove_tag(
    user_id: UUID,
    tag: str,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Remove a tag from a user's profile."""
    try:
        success = profile_service.remove_tag(UserId(user_id), tag)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile or tag not found"
            )
        
        return {"message": f"Tag '{tag}' removed successfully"}
    except Exception as e:
        logger.error(f"Error removing tag from user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove tag"
        )


@router.post("/{user_id}/availability")
async def add_availability_window(
    user_id: UUID,
    availability_data: AvailabilityWindowSchema,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Add an availability window to a user's profile."""
    try:
        window = _convert_availability_schema_to_domain(availability_data)
        success = profile_service.add_availability_window(UserId(user_id), window)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return {"message": "Availability window added successfully"}
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error adding availability window to user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add availability window"
        )


@router.delete("/{user_id}/availability")
async def remove_availability_window(
    user_id: UUID,
    availability_data: AvailabilityWindowSchema,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Remove an availability window from a user's profile."""
    try:
        window = _convert_availability_schema_to_domain(availability_data)
        success = profile_service.remove_availability_window(UserId(user_id), window)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile or availability window not found"
            )
        
        return {"message": "Availability window removed successfully"}
    except Exception as e:
        logger.error(f"Error removing availability window from user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove availability window"
        )


@router.get("/search/by-skills", response_model=List[ProfileResponseSchema])
async def search_profiles_by_skills(
    skills: List[str],
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Search profiles by skills."""
    try:
        profiles = profile_service.get_profiles_by_skills(skills)
        return [_convert_profile_to_response(profile) for profile in profiles]
    except Exception as e:
        logger.error(f"Error searching profiles by skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search profiles"
        )


@router.get("/search/by-tags", response_model=List[ProfileResponseSchema])
async def search_profiles_by_tags(
    tags: List[str],
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Search profiles by tags."""
    try:
        profiles = profile_service.get_profiles_by_tags(tags)
        return [_convert_profile_to_response(profile) for profile in profiles]
    except Exception as e:
        logger.error(f"Error searching profiles by tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search profiles"
        )


@router.get("/{user_id}/stats", response_model=ProfileStatsSchema)
async def get_profile_stats(
    user_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get volunteer statistics for a user profile."""
    try:
        stats = history_service.get_volunteer_statistics(UserId(user_id))
        return ProfileStatsSchema(**stats)
    except Exception as e:
        logger.error(f"Error getting profile stats for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile statistics"
        )


@router.delete("/{user_id}")
async def delete_profile(
    user_id: UUID,
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Delete a user's profile."""
    try:
        success = profile_service.delete_profile(UserId(user_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return {"message": "Profile deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting profile for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile"
        )

#endregion