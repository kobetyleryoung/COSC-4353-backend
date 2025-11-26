from __future__ import annotations
from datetime import datetime, time
from typing import List, Optional
from uuid import uuid4
from logging import Logger


from src.domain.profiles import Profile, AvailabilityWindow, Skill
from src.domain.users import UserId
from src.domain.repositories import ProfileRepository


class ProfileManagementService:
    """Service for managing user profiles including location, skills, preferences, and availability."""
    
    def __init__(self, logger: Logger, profile_repository: ProfileRepository):
        self._logger = logger
        self._profile_repository = profile_repository
    
    def create_profile(
        self,
        user_id: UserId,
        display_name: str,
        phone: Optional[str] = None,
        skills: Optional[List[Skill]] = None,
        tags: Optional[List[str]] = None,
        availability: Optional[List[AvailabilityWindow]] = None
    ) -> Profile:
        """Create a new user profile."""
        # Validation
        existing_profile = self._profile_repository.get(user_id)
        if existing_profile:
            raise ValueError("Profile already exists for this user")
        
        if not display_name or len(display_name.strip()) == 0:
            raise ValueError("Display name is required")
        if len(display_name) > 100:
            raise ValueError("Display name must be 100 characters or less")
        
        if phone and len(phone) > 20:
            raise ValueError("Phone number must be 20 characters or less")
        
        if phone and not self._validate_phone(phone):
            raise ValueError("Phone number format is invalid")
        
        if skills and len(skills) > 50:
            raise ValueError("Cannot have more than 50 skills")
        
        if tags and len(tags) > 20:
            raise ValueError("Cannot have more than 20 tags")
        
        # Validate availability windows
        if availability:
            for window in availability:
                if not self._validate_availability_window(window):
                    raise ValueError("Invalid availability window")
        
        # Create profile
        profile = Profile(
            user_id=user_id,
            display_name=display_name.strip(),
            phone=phone.strip() if phone else None,
            skills=skills or [],
            tags=tags or [],
            availability=availability or [],
            updated_at=datetime.now()
        )
        
        self._profile_repository.save(profile)
        self._logger.info(f"Created profile for user: {display_name} (ID: {user_id.value})")
        
        return profile
    
    def get_profile_by_user_id(self, user_id: UserId) -> Optional[Profile]:
        """Retrieve a profile by user ID."""
        return self._profile_repository.get(user_id)
    
    def update_profile(
        self,
        user_id: UserId,
        display_name: Optional[str] = None,
        phone: Optional[str] = None,
        skills: Optional[List[Skill]] = None,
        tags: Optional[List[str]] = None,
        availability: Optional[List[AvailabilityWindow]] = None
    ) -> Optional[Profile]:
        """Update an existing profile."""
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            return None
        
        # Validation for updates
        if display_name is not None:
            if not display_name or len(display_name.strip()) == 0:
                raise ValueError("Display name cannot be empty")
            if len(display_name) > 100:
                raise ValueError("Display name must be 100 characters or less")
            profile.display_name = display_name.strip()
        
        if phone is not None:
            if phone and len(phone) > 20:
                raise ValueError("Phone number must be 20 characters or less")
            if phone and not self._validate_phone(phone):
                raise ValueError("Phone number format is invalid")
            profile.phone = phone.strip() if phone else None
        
        if skills is not None:
            if len(skills) > 50:
                raise ValueError("Cannot have more than 50 skills")
            profile.skills = skills
        
        if tags is not None:
            if len(tags) > 20:
                raise ValueError("Cannot have more than 20 tags")
            profile.tags = tags
        
        if availability is not None:
            for window in availability:
                if not self._validate_availability_window(window):
                    raise ValueError("Invalid availability window")
            profile.availability = availability
        
        profile.updated_at = datetime.now()
        self._profile_repository.save(profile)
        self._logger.info(f"Updated profile for user: {profile.display_name} (ID: {user_id.value})")
        
        return profile
    
    def add_skill(self, user_id: UserId, skill: Skill) -> bool:
        """Add a skill to a user's profile."""
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            return False
        
        if not skill or len(skill.strip()) == 0:
            raise ValueError("Skill cannot be empty")
        
        skill = skill.strip()
        if skill in profile.skills:
            return True  # Already exists
        
        if len(profile.skills) >= 50:
            raise ValueError("Cannot have more than 50 skills")
        
        profile.skills.append(skill)
        profile.updated_at = datetime.now()
        self._profile_repository.save(profile)
        self._logger.info(f"Added skill '{skill}' to user {user_id.value}")
        return True
    
    def remove_skill(self, user_id: UserId, skill: Skill) -> bool:
        """Remove a skill from a user's profile."""
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            return False
        
        if skill in profile.skills:
            profile.skills.remove(skill)
            profile.updated_at = datetime.now()
            self._profile_repository.save(profile)
            self._logger.info(f"Removed skill '{skill}' from user {user_id.value}")
            return True
        
        return False
    
    def add_tag(self, user_id: UserId, tag: str) -> bool:
        """Add a tag to a user's profile."""
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            return False
        
        if not tag or len(tag.strip()) == 0:
            raise ValueError("Tag cannot be empty")
        
        tag = tag.strip().lower()
        if tag in profile.tags:
            return True  # Already exists
        
        if len(profile.tags) >= 20:
            raise ValueError("Cannot have more than 20 tags")
        
        profile.tags.append(tag)
        profile.updated_at = datetime.now()
        self._profile_repository.save(profile)
        self._logger.info(f"Added tag '{tag}' to user {user_id.value}")
        
        return True
    
    def remove_tag(self, user_id: UserId, tag: str) -> bool:
        """Remove a tag from a user's profile."""
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            return False
        
        tag = tag.strip().lower()
        if tag in profile.tags:
            profile.tags.remove(tag)
            profile.updated_at = datetime.now()
            self._profile_repository.save(profile)
            self._logger.info(f"Removed tag '{tag}' from user {user_id.value}")
            return True
        
        return False
    
    def add_availability_window(self, user_id: UserId, window: AvailabilityWindow) -> bool:
        """Add an availability window to a user's profile."""
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            return False
        
        if not self._validate_availability_window(window):
            raise ValueError("Invalid availability window")
        
        # Check for overlapping windows on the same day
        for existing_window in profile.availability:
            if existing_window.weekday == window.weekday:
                if self._windows_overlap(existing_window, window):
                    raise ValueError("Availability window overlaps with existing window")
        
        profile.availability.append(window)
        profile.updated_at = datetime.now()
        self._profile_repository.save(profile)
        self._logger.info(f"Added availability window to user {user_id.value}")
        
        return True
    
    def remove_availability_window(self, user_id: UserId, window: AvailabilityWindow) -> bool:
        """Remove an availability window from a user's profile."""
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            return False
        
        for i, existing_window in enumerate(profile.availability):
            if (existing_window.weekday == window.weekday and
                existing_window.start == window.start and
                existing_window.end == window.end):
                profile.availability.pop(i)
                profile.updated_at = datetime.now()
                self._profile_repository.save(profile)
                self._logger.info(f"Removed availability window from user {user_id.value}")
                return True
        
        return False
    
    def delete_profile(self, user_id: UserId) -> bool:
        """Delete a user's profile."""
        profile = self._profile_repository.get(user_id)
        if not profile:
            return False
        
        # Note: Repository protocol doesn't include delete() method yet
        self._logger.warning(f"Delete profile requested but not fully implemented for user ID: {user_id.value}")
        return False
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        import re
        # Simple phone validation - allows various formats
        phone_pattern = r'^[\+]?[\d\s\-\(\)]{10,20}$'
        return bool(re.match(phone_pattern, phone.strip()))
    
    def _validate_availability_window(self, window: AvailabilityWindow) -> bool:
        """Validate an availability window."""
        # Check weekday is valid (0-6)
        if window.weekday < 0 or window.weekday > 6:
            return False
        
        # Check start time is before end time
        if window.start >= window.end:
            return False
        
        return True
    
    def _windows_overlap(self, window1: AvailabilityWindow, window2: AvailabilityWindow) -> bool:
        """Check if two availability windows overlap."""
        if window1.weekday != window2.weekday:
            return False
        
        return not (window1.end <= window2.start or window2.end <= window1.start)
