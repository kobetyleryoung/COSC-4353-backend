from __future__ import annotations
from datetime import datetime, time
from typing import List, Optional
from uuid import uuid4
from logging import Logger


from src.domain.profiles import Profile, AvailabilityWindow, Skill
from src.domain.users import UserId


class ProfileManagementService:
    """Service for managing user profiles including location, skills, preferences, and availability."""
    
    def __init__(self, logger: Logger):
        self._logger = logger
        # Hard-coded data storage (no database implementation)
        self._profiles: dict[str, Profile] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self) -> None:
        """Initialize with sample user profiles."""
        # Sample profile 1
        user1_id = UserId.new()
        profile1 = Profile(
            user_id=user1_id,
            display_name="John Smith",
            phone="555-123-4567",
            skills=["Physical Labor", "Customer Service", "First Aid"],
            tags=["spanish", "driver", "experience"],
            availability=[
                AvailabilityWindow(weekday=1, start=time(9, 0), end=time(17, 0)),  # Tuesday
                AvailabilityWindow(weekday=5, start=time(10, 0), end=time(16, 0)),  # Saturday
                AvailabilityWindow(weekday=6, start=time(8, 0), end=time(12, 0)),   # Sunday
            ],
            updated_at=datetime.now()
        )
        self._profiles[str(user1_id.value)] = profile1
        
        # Sample profile 2
        user2_id = UserId.new()
        profile2 = Profile(
            user_id=user2_id,
            display_name="Sarah Johnson",
            phone="555-987-6543",
            skills=["Communication", "Organization", "Teaching", "Event Planning"],
            tags=["bilingual", "experience", "leadership"],
            availability=[
                AvailabilityWindow(weekday=2, start=time(14, 0), end=time(18, 0)),  # Wednesday
                AvailabilityWindow(weekday=3, start=time(10, 0), end=time(15, 0)),  # Thursday
                AvailabilityWindow(weekday=6, start=time(9, 0), end=time(14, 0)),   # Sunday
            ],
            updated_at=datetime.now()
        )
        self._profiles[str(user2_id.value)] = profile2
        
        # Sample profile 3
        user3_id = UserId.new()
        profile3 = Profile(
            user_id=user3_id,
            display_name="Mike Davis",
            phone="555-456-7890",
            skills=["Environmental Awareness", "Physical Labor", "Patience"],
            tags=["outdoors", "environmental", "youth"],
            availability=[
                AvailabilityWindow(weekday=0, start=time(18, 0), end=time(21, 0)),  # Monday
                AvailabilityWindow(weekday=4, start=time(17, 0), end=time(20, 0)),  # Friday
                AvailabilityWindow(weekday=5, start=time(8, 0), end=time(18, 0)),   # Saturday
            ],
            updated_at=datetime.now()
        )
        self._profiles[str(user3_id.value)] = profile3
        
        self._logger.info(f"Initialized {len(self._profiles)} sample profiles")
    
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
        if str(user_id.value) in self._profiles:
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
        
        self._profiles[str(user_id.value)] = profile
        self._logger.info(f"Created profile for user: {display_name} (ID: {user_id.value})")
        
        return profile
    
    def get_profile_by_user_id(self, user_id: UserId) -> Optional[Profile]:
        """Retrieve a profile by user ID."""
        return self._profiles.get(str(user_id.value))
    
    def get_all_profiles(self) -> List[Profile]:
        """Retrieve all profiles."""
        return list(self._profiles.values())
    
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
                self._logger.info(f"Removed availability window from user {user_id.value}")
                return True
        
        return False
    
    def get_profiles_by_skills(self, skills: List[Skill]) -> List[Profile]:
        """Get profiles that have any of the specified skills."""
        matching_profiles = []
        skill_set = set(skill.lower() for skill in skills)
        
        for profile in self._profiles.values():
            profile_skills = set(skill.lower() for skill in profile.skills)
            if skill_set.intersection(profile_skills):
                matching_profiles.append(profile)
        
        return matching_profiles
    
    def get_profiles_by_tags(self, tags: List[str]) -> List[Profile]:
        """Get profiles that have any of the specified tags."""
        matching_profiles = []
        tag_set = set(tag.lower() for tag in tags)
        
        for profile in self._profiles.values():
            profile_tags = set(tag.lower() for tag in profile.tags)
            if tag_set.intersection(profile_tags):
                matching_profiles.append(profile)
        
        return matching_profiles
    
    def get_available_profiles(self, weekday: int, start_time: time, end_time: time) -> List[Profile]:
        """Get profiles that are available during the specified time window."""
        available_profiles = []
        
        for profile in self._profiles.values():
            for window in profile.availability:
                if (window.weekday == weekday and
                    window.start <= start_time and
                    window.end >= end_time):
                    available_profiles.append(profile)
                    break
        
        return available_profiles
    
    def delete_profile(self, user_id: UserId) -> bool:
        """Delete a user's profile."""
        if str(user_id.value) not in self._profiles:
            return False
        
        profile = self._profiles.pop(str(user_id.value))
        self._logger.info(f"Deleted profile for user: {profile.display_name} (ID: {user_id.value})")
        return True
    
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
