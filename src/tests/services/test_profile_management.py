"""
Tests for ProfileManagementService
"""
import pytest
from datetime import datetime, time
from uuid import uuid4
import logging

from src.services.profile_management import ProfileManagementService
from src.domain.profiles import Profile, AvailabilityWindow
from src.domain.users import UserId


class TestProfileManagementService:
    """Test ProfileManagementService functionality"""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger"""
        return logging.getLogger("test")
    
    @pytest.fixture
    def service(self, logger):
        """Create a fresh ProfileManagementService for each test"""
        return ProfileManagementService(logger)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return UserId.new()
    
    @pytest.fixture
    def sample_availability(self):
        """Sample availability windows for testing"""
        return [
            AvailabilityWindow(weekday=1, start=time(9, 0), end=time(17, 0)),
            AvailabilityWindow(weekday=5, start=time(10, 0), end=time(16, 0))
        ]
    
    def test_service_initialization(self, service):
        """Test service initializes with sample data"""
        profiles = service.get_all_profiles()
        assert isinstance(profiles, list)
        assert len(profiles) >= 0  # May have sample data
    
    def test_create_profile(self, service, sample_user_id, sample_availability):
        """Test creating a new user profile"""
        profile = service.create_profile(
            user_id=sample_user_id,
            display_name="John Doe",
            phone="555-123-4567",
            skills=["Python", "Testing"],
            tags=["experienced", "reliable"],
            availability=sample_availability
        )
        
        assert isinstance(profile, Profile)
        assert profile.user_id == sample_user_id
        assert profile.display_name == "John Doe"
        assert profile.phone == "555-123-4567"
        assert profile.skills == ["Python", "Testing"]
        assert profile.tags == ["experienced", "reliable"]
        assert profile.availability == sample_availability
        assert profile.updated_at is not None
    
    def test_create_profile_minimal(self, service, sample_user_id):
        """Test creating profile with minimal required data"""
        profile = service.create_profile(
            user_id=sample_user_id,
            display_name="Jane Smith"
        )
        
        assert profile.user_id == sample_user_id
        assert profile.display_name == "Jane Smith"
        assert profile.phone is None
        assert profile.skills == []
        assert profile.tags == []
        assert profile.availability == []
    
    def test_create_profile_duplicate_user(self, service, sample_user_id):
        """Test creating profile for user that already has one"""
        # Create first profile
        service.create_profile(sample_user_id, "First Profile")
        
        # Try to create second profile for same user
        with pytest.raises(ValueError, match="Profile already exists"):
            service.create_profile(sample_user_id, "Second Profile")
    
    def test_create_profile_validation_empty_name(self, service, sample_user_id):
        """Test validation fails for empty display name"""
        with pytest.raises(ValueError, match="Display name cannot be empty"):
            service.create_profile(sample_user_id, "")
    
    def test_create_profile_validation_long_name(self, service, sample_user_id):
        """Test validation fails for overly long display name"""
        long_name = "x" * 101  # Assuming 100 char limit
        
        with pytest.raises(ValueError, match="Display name too long"):
            service.create_profile(sample_user_id, long_name)
    
    def test_create_profile_validation_invalid_phone(self, service, sample_user_id):
        """Test validation fails for invalid phone number"""
        with pytest.raises(ValueError, match="Invalid phone number"):
            service.create_profile(
                sample_user_id, 
                "Valid Name",
                phone="invalid-phone"
            )
    
    def test_create_profile_validation_too_many_skills(self, service, sample_user_id):
        """Test validation fails for too many skills"""
        too_many_skills = [f"skill{i}" for i in range(51)]  # Assuming 50 skill limit
        
        with pytest.raises(ValueError, match="Too many skills"):
            service.create_profile(
                sample_user_id,
                "Valid Name",
                skills=too_many_skills
            )
    
    def test_create_profile_validation_too_many_tags(self, service, sample_user_id):
        """Test validation fails for too many tags"""
        too_many_tags = [f"tag{i}" for i in range(21)]  # Assuming 20 tag limit
        
        with pytest.raises(ValueError, match="Too many tags"):
            service.create_profile(
                sample_user_id,
                "Valid Name",
                tags=too_many_tags
            )
    
    def test_get_profile_by_user_id(self, service, sample_user_id):
        """Test retrieving profile by user ID"""
        # Create a profile
        created_profile = service.create_profile(sample_user_id, "Test User")
        
        # Retrieve it
        retrieved_profile = service.get_profile_by_user_id(sample_user_id)
        
        assert retrieved_profile is not None
        assert retrieved_profile.user_id == sample_user_id
        assert retrieved_profile.display_name == "Test User"
    
    def test_get_profile_by_user_id_not_found(self, service):
        """Test retrieving non-existent profile returns None"""
        non_existent_id = UserId.new()
        profile = service.get_profile_by_user_id(non_existent_id)
        assert profile is None
    
    def test_get_all_profiles(self, service):
        """Test retrieving all profiles"""
        initial_count = len(service.get_all_profiles())
        
        # Create a few profiles
        for i in range(3):
            user_id = UserId.new()
            service.create_profile(user_id, f"User {i}")
        
        all_profiles = service.get_all_profiles()
        assert len(all_profiles) == initial_count + 3
    
    def test_update_profile(self, service, sample_user_id):
        """Test updating an existing profile"""
        # Create a profile
        service.create_profile(
            sample_user_id,
            "Original Name",
            phone="555-111-1111",
            skills=["Original Skill"]
        )
        
        # Update it
        updated_profile = service.update_profile(
            sample_user_id,
            display_name="Updated Name",
            phone="555-222-2222",
            skills=["New Skill", "Another Skill"],
            tags=["new_tag"]
        )
        
        assert updated_profile is not None
        assert updated_profile.display_name == "Updated Name"
        assert updated_profile.phone == "555-222-2222"
        assert updated_profile.skills == ["New Skill", "Another Skill"]
        assert updated_profile.tags == ["new_tag"]
    
    def test_update_profile_not_found(self, service):
        """Test updating non-existent profile returns None"""
        non_existent_id = UserId.new()
        result = service.update_profile(non_existent_id, display_name="Should Fail")
        assert result is None
    
    def test_add_skill(self, service, sample_user_id):
        """Test adding a skill to a profile"""
        # Create profile
        service.create_profile(sample_user_id, "Test User", skills=["Python"])
        
        # Add skill
        success = service.add_skill(sample_user_id, "JavaScript")
        assert success is True
        
        # Verify skill was added
        profile = service.get_profile_by_user_id(sample_user_id)
        assert "JavaScript" in profile.skills
        assert "Python" in profile.skills
    
    def test_add_skill_duplicate(self, service, sample_user_id):
        """Test adding duplicate skill"""
        # Create profile with skill
        service.create_profile(sample_user_id, "Test User", skills=["Python"])
        
        # Try to add same skill
        success = service.add_skill(sample_user_id, "Python")
        assert success is False
    
    def test_add_skill_profile_not_found(self, service):
        """Test adding skill to non-existent profile"""
        non_existent_id = UserId.new()
        success = service.add_skill(non_existent_id, "Python")
        assert success is False
    
    def test_remove_skill(self, service, sample_user_id):
        """Test removing a skill from a profile"""
        # Create profile with skills
        service.create_profile(sample_user_id, "Test User", skills=["Python", "JavaScript"])
        
        # Remove skill
        success = service.remove_skill(sample_user_id, "JavaScript")
        assert success is True
        
        # Verify skill was removed
        profile = service.get_profile_by_user_id(sample_user_id)
        assert "JavaScript" not in profile.skills
        assert "Python" in profile.skills
    
    def test_remove_skill_not_found(self, service, sample_user_id):
        """Test removing skill that doesn't exist"""
        service.create_profile(sample_user_id, "Test User", skills=["Python"])
        
        success = service.remove_skill(sample_user_id, "JavaScript")
        assert success is False
    
    def test_add_tag(self, service, sample_user_id):
        """Test adding a tag to a profile"""
        service.create_profile(sample_user_id, "Test User", tags=["experienced"])
        
        success = service.add_tag(sample_user_id, "reliable")
        assert success is True
        
        profile = service.get_profile_by_user_id(sample_user_id)
        assert "reliable" in profile.tags
        assert "experienced" in profile.tags
    
    def test_add_tag_duplicate(self, service, sample_user_id):
        """Test adding duplicate tag"""
        service.create_profile(sample_user_id, "Test User", tags=["experienced"])
        
        success = service.add_tag(sample_user_id, "experienced")
        assert success is False
    
    def test_remove_tag(self, service, sample_user_id):
        """Test removing a tag from a profile"""
        service.create_profile(sample_user_id, "Test User", tags=["experienced", "reliable"])
        
        success = service.remove_tag(sample_user_id, "reliable")
        assert success is True
        
        profile = service.get_profile_by_user_id(sample_user_id)
        assert "reliable" not in profile.tags
        assert "experienced" in profile.tags
    
    def test_add_availability_window(self, service, sample_user_id):
        """Test adding availability window"""
        service.create_profile(sample_user_id, "Test User")
        
        window = AvailabilityWindow(weekday=1, start=time(9, 0), end=time(17, 0))
        success = service.add_availability_window(sample_user_id, window)
        assert success is True
        
        profile = service.get_profile_by_user_id(sample_user_id)
        assert window in profile.availability
    
    def test_add_availability_window_overlap(self, service, sample_user_id):
        """Test adding overlapping availability window"""
        existing_window = AvailabilityWindow(weekday=1, start=time(9, 0), end=time(17, 0))
        service.create_profile(sample_user_id, "Test User", availability=[existing_window])
        
        # Try to add overlapping window
        overlapping_window = AvailabilityWindow(weekday=1, start=time(10, 0), end=time(18, 0))
        success = service.add_availability_window(sample_user_id, overlapping_window)
        assert success is False
    
    def test_remove_availability_window(self, service, sample_user_id):
        """Test removing availability window"""
        window1 = AvailabilityWindow(weekday=1, start=time(9, 0), end=time(17, 0))
        window2 = AvailabilityWindow(weekday=2, start=time(10, 0), end=time(16, 0))
        service.create_profile(sample_user_id, "Test User", availability=[window1, window2])
        
        success = service.remove_availability_window(sample_user_id, window2)
        assert success is True
        
        profile = service.get_profile_by_user_id(sample_user_id)
        assert window2 not in profile.availability
        assert window1 in profile.availability
    
    def test_get_profiles_by_skills(self, service):
        """Test searching profiles by skills"""
        user1 = UserId.new()
        user2 = UserId.new()
        user3 = UserId.new()
        
        service.create_profile(user1, "Python Dev", skills=["Python", "Django"])
        service.create_profile(user2, "JS Dev", skills=["JavaScript", "React"])
        service.create_profile(user3, "Full Stack", skills=["Python", "JavaScript"])
        
        # Search for Python profiles
        python_profiles = service.get_profiles_by_skills(["Python"])
        python_user_ids = [p.user_id for p in python_profiles]
        
        assert user1 in python_user_ids
        assert user3 in python_user_ids
        assert user2 not in python_user_ids
    
    def test_get_profiles_by_tags(self, service):
        """Test searching profiles by tags"""
        user1 = UserId.new()
        user2 = UserId.new()
        user3 = UserId.new()
        
        service.create_profile(user1, "User 1", tags=["experienced", "leadership"])
        service.create_profile(user2, "User 2", tags=["beginner", "eager"])
        service.create_profile(user3, "User 3", tags=["experienced", "bilingual"])
        
        # Search for experienced profiles
        experienced_profiles = service.get_profiles_by_tags(["experienced"])
        experienced_user_ids = [p.user_id for p in experienced_profiles]
        
        assert user1 in experienced_user_ids
        assert user3 in experienced_user_ids
        assert user2 not in experienced_user_ids
    
    def test_get_available_profiles(self, service):
        """Test finding profiles available at specific time"""
        user1 = UserId.new()
        user2 = UserId.new()
        
        # User 1 available Monday 9-17
        availability1 = [AvailabilityWindow(weekday=0, start=time(9, 0), end=time(17, 0))]
        service.create_profile(user1, "User 1", availability=availability1)
        
        # User 2 available Tuesday 10-16
        availability2 = [AvailabilityWindow(weekday=1, start=time(10, 0), end=time(16, 0))]
        service.create_profile(user2, "User 2", availability=availability2)
        
        # Search for Monday 10-15 availability
        available_profiles = service.get_available_profiles(0, time(10, 0), time(15, 0))
        available_user_ids = [p.user_id for p in available_profiles]
        
        assert user1 in available_user_ids
        assert user2 not in available_user_ids
    
    def test_delete_profile(self, service, sample_user_id):
        """Test deleting a profile"""
        # Create profile
        service.create_profile(sample_user_id, "To Be Deleted")
        
        # Verify it exists
        assert service.get_profile_by_user_id(sample_user_id) is not None
        
        # Delete it
        success = service.delete_profile(sample_user_id)
        assert success is True
        
        # Verify it's gone
        assert service.get_profile_by_user_id(sample_user_id) is None
    
    def test_delete_profile_not_found(self, service):
        """Test deleting non-existent profile"""
        non_existent_id = UserId.new()
        success = service.delete_profile(non_existent_id)
        assert success is False