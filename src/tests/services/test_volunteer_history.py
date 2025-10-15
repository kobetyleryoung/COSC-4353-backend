"""
Tests for VolunteerHistoryService
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from src.services.volunteer_history import VolunteerHistoryService
from src.domain.volunteering import VolunteerHistoryEntry, VolunteerHistoryEntryId
from src.domain.events import EventId
from src.domain.users import UserId


class TestVolunteerHistoryService:
    """Test VolunteerHistoryService functionality"""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger"""
        return logging.getLogger("test")
    
    @pytest.fixture
    def service(self, logger):
        """Create a fresh VolunteerHistoryService for each test"""
        return VolunteerHistoryService(logger)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return UserId.new()
    
    @pytest.fixture
    def sample_event_id(self):
        """Sample event ID for testing"""
        return EventId.new()
    
    def test_service_initialization(self, service):
        """Test service initializes with sample data"""
        entries = service.get_recent_history()
        assert isinstance(entries, list)
        assert len(entries) >= 0  # May have sample data
    
    def test_create_history_entry(self, service, sample_user_id, sample_event_id):
        """Test creating a new volunteer history entry"""
        entry_date = datetime.now() - timedelta(days=1)
        
        entry = service.create_history_entry(
            user_id=sample_user_id,
            event_id=sample_event_id,
            role="General Volunteer",
            hours=4.5,
            date=entry_date,
            notes="Great experience helping at the event"
        )
        
        assert isinstance(entry, VolunteerHistoryEntry)
        assert entry.user_id == sample_user_id
        assert entry.event_id == sample_event_id
        assert entry.role == "General Volunteer"
        assert entry.hours == 4.5
        assert entry.date == entry_date
        assert entry.notes == "Great experience helping at the event"
    
    def test_create_history_entry_minimal(self, service, sample_user_id, sample_event_id):
        """Test creating history entry with minimal required data"""
        entry_date = datetime.now() - timedelta(days=1)
        
        entry = service.create_history_entry(
            user_id=sample_user_id,
            event_id=sample_event_id,
            role="Volunteer",
            hours=2.0,
            date=entry_date
        )
        
        assert entry.notes is None
        assert entry.hours == 2.0
        assert entry.role == "Volunteer"
    
    def test_create_history_entry_validation_empty_role(self, service, sample_user_id, sample_event_id):
        """Test validation fails for empty role"""
        with pytest.raises(ValueError, match="Role cannot be empty"):
            service.create_history_entry(
                user_id=sample_user_id,
                event_id=sample_event_id,
                role="",
                hours=4.0,
                date=datetime.now() - timedelta(days=1)
            )
    
    def test_create_history_entry_validation_long_role(self, service, sample_user_id, sample_event_id):
        """Test validation fails for overly long role"""
        long_role = "x" * 101  # Assuming 100 char limit
        
        with pytest.raises(ValueError, match="Role too long"):
            service.create_history_entry(
                user_id=sample_user_id,
                event_id=sample_event_id,
                role=long_role,
                hours=4.0,
                date=datetime.now() - timedelta(days=1)
            )
    
    def test_create_history_entry_validation_negative_hours(self, service, sample_user_id, sample_event_id):
        """Test validation fails for negative hours"""
        with pytest.raises(ValueError, match="Hours must be positive"):
            service.create_history_entry(
                user_id=sample_user_id,
                event_id=sample_event_id,
                role="Volunteer",
                hours=-1.0,
                date=datetime.now() - timedelta(days=1)
            )
    
    def test_create_history_entry_validation_too_many_hours(self, service, sample_user_id, sample_event_id):
        """Test validation fails for too many hours"""
        with pytest.raises(ValueError, match="Hours cannot exceed 24"):
            service.create_history_entry(
                user_id=sample_user_id,
                event_id=sample_event_id,
                role="Volunteer",
                hours=25.0,
                date=datetime.now() - timedelta(days=1)
            )
    
    def test_create_history_entry_validation_future_date(self, service, sample_user_id, sample_event_id):
        """Test validation fails for future date"""
        future_date = datetime.now() + timedelta(days=1)
        
        with pytest.raises(ValueError, match="Date cannot be in the future"):
            service.create_history_entry(
                user_id=sample_user_id,
                event_id=sample_event_id,
                role="Volunteer",
                hours=4.0,
                date=future_date
            )
    
    def test_create_history_entry_validation_long_notes(self, service, sample_user_id, sample_event_id):
        """Test validation fails for overly long notes"""
        long_notes = "x" * 1001  # Assuming 1000 char limit
        
        with pytest.raises(ValueError, match="Notes too long"):
            service.create_history_entry(
                user_id=sample_user_id,
                event_id=sample_event_id,
                role="Volunteer",
                hours=4.0,
                date=datetime.now() - timedelta(days=1),
                notes=long_notes
            )
    
    def test_create_history_entry_duplicate(self, service, sample_user_id, sample_event_id):
        """Test creating duplicate entry fails"""
        entry_date = datetime.now() - timedelta(days=1)
        
        # Create first entry
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=sample_event_id,
            role="Volunteer",
            hours=4.0,
            date=entry_date
        )
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="Duplicate entry"):
            service.create_history_entry(
                user_id=sample_user_id,
                event_id=sample_event_id,
                role="Different Role",  # Even with different role, same user/event/date
                hours=2.0,
                date=entry_date
            )
    
    def test_get_history_entry_by_id(self, service, sample_user_id, sample_event_id):
        """Test retrieving history entry by ID"""
        entry = service.create_history_entry(
            user_id=sample_user_id,
            event_id=sample_event_id,
            role="Test Role",
            hours=3.0,
            date=datetime.now() - timedelta(days=1)
        )
        
        retrieved_entry = service.get_history_entry_by_id(entry.id)
        assert retrieved_entry is not None
        assert retrieved_entry.id == entry.id
        assert retrieved_entry.role == "Test Role"
    
    def test_get_history_entry_by_id_not_found(self, service):
        """Test retrieving non-existent entry returns None"""
        fake_id = VolunteerHistoryEntryId(uuid4())
        entry = service.get_history_entry_by_id(fake_id)
        assert entry is None
    
    def test_get_user_history(self, service, sample_user_id):
        """Test getting all history entries for a user"""
        event1_id = EventId.new()
        event2_id = EventId.new()
        
        # Create entries for the user
        entry1 = service.create_history_entry(
            user_id=sample_user_id,
            event_id=event1_id,
            role="Role 1",
            hours=4.0,
            date=datetime.now() - timedelta(days=1)
        )
        
        entry2 = service.create_history_entry(
            user_id=sample_user_id,
            event_id=event2_id,
            role="Role 2",
            hours=3.0,
            date=datetime.now() - timedelta(days=2)
        )
        
        user_history = service.get_user_history(sample_user_id)
        entry_ids = [e.id for e in user_history]
        
        assert entry1.id in entry_ids
        assert entry2.id in entry_ids
    
    def test_get_event_history(self, service, sample_event_id):
        """Test getting all history entries for an event"""
        user1_id = UserId.new()
        user2_id = UserId.new()
        
        # Create entries for the event
        entry1 = service.create_history_entry(
            user_id=user1_id,
            event_id=sample_event_id,
            role="Volunteer 1",
            hours=4.0,
            date=datetime.now() - timedelta(days=1)
        )
        
        entry2 = service.create_history_entry(
            user_id=user2_id,
            event_id=sample_event_id,
            role="Volunteer 2",
            hours=3.0,
            date=datetime.now() - timedelta(days=1)
        )
        
        event_history = service.get_event_history(sample_event_id)
        entry_ids = [e.id for e in event_history]
        
        assert entry1.id in entry_ids
        assert entry2.id in entry_ids
    
    def test_get_user_total_hours(self, service, sample_user_id):
        """Test calculating total volunteer hours for a user"""
        event1_id = EventId.new()
        event2_id = EventId.new()
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event1_id,
            role="Volunteer",
            hours=4.5,
            date=datetime.now() - timedelta(days=1)
        )
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event2_id,
            role="Volunteer",
            hours=3.0,
            date=datetime.now() - timedelta(days=2)
        )
        
        total_hours = service.get_user_total_hours(sample_user_id)
        assert total_hours == 7.5
    
    def test_get_user_hours_in_period(self, service, sample_user_id):
        """Test calculating user hours within a specific period"""
        event1_id = EventId.new()
        event2_id = EventId.new()
        event3_id = EventId.new()
        
        # Entry within period
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event1_id,
            role="Volunteer",
            hours=4.0,
            date=datetime.now() - timedelta(days=5)
        )
        
        # Entry within period
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event2_id,
            role="Volunteer",
            hours=3.0,
            date=datetime.now() - timedelta(days=3)
        )
        
        # Entry outside period
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event3_id,
            role="Volunteer",
            hours=2.0,
            date=datetime.now() - timedelta(days=15)
        )
        
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now() - timedelta(days=1)
        
        period_hours = service.get_user_hours_in_period(sample_user_id, start_date, end_date)
        assert period_hours == 7.0  # 4.0 + 3.0, excluding the 2.0 from outside period
    
    def test_get_user_event_count(self, service, sample_user_id):
        """Test counting unique events a user has volunteered for"""
        event1_id = EventId.new()
        event2_id = EventId.new()
        
        # Two entries for event1, one for event2
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event1_id,
            role="Role 1",
            hours=4.0,
            date=datetime.now() - timedelta(days=1)
        )
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event2_id,
            role="Role 2",
            hours=3.0,
            date=datetime.now() - timedelta(days=2)
        )
        
        event_count = service.get_user_event_count(sample_user_id)
        assert event_count == 2
    
    def test_get_user_roles(self, service, sample_user_id):
        """Test getting unique roles a user has performed"""
        event1_id = EventId.new()
        event2_id = EventId.new()
        event3_id = EventId.new()
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event1_id,
            role="Volunteer",
            hours=4.0,
            date=datetime.now() - timedelta(days=1)
        )
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event2_id,
            role="Team Leader",
            hours=5.0,
            date=datetime.now() - timedelta(days=2)
        )
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event3_id,
            role="Volunteer",  # Duplicate role
            hours=3.0,
            date=datetime.now() - timedelta(days=3)
        )
        
        roles = service.get_user_roles(sample_user_id)
        assert "Volunteer" in roles
        assert "Team Leader" in roles
        assert len(roles) == 2  # Should be unique roles only
    
    def test_get_recent_history(self, service):
        """Test getting recent volunteer history"""
        user_id = UserId.new()
        event_id = EventId.new()
        
        # Create recent entry
        recent_entry = service.create_history_entry(
            user_id=user_id,
            event_id=event_id,
            role="Recent Volunteer",
            hours=4.0,
            date=datetime.now() - timedelta(days=5)
        )
        
        recent_history = service.get_recent_history(days=7)
        entry_ids = [e.id for e in recent_history]
        
        assert recent_entry.id in entry_ids
    
    def test_get_top_volunteers_by_hours(self, service):
        """Test getting top volunteers by total hours"""
        # Create volunteers with different hour totals
        user1 = UserId.new()
        user2 = UserId.new()
        user3 = UserId.new()
        
        # User 1: 10 hours total
        service.create_history_entry(user1, EventId.new(), "Volunteer", 6.0, datetime.now() - timedelta(days=1))
        service.create_history_entry(user1, EventId.new(), "Volunteer", 4.0, datetime.now() - timedelta(days=2))
        
        # User 2: 15 hours total
        service.create_history_entry(user2, EventId.new(), "Volunteer", 8.0, datetime.now() - timedelta(days=1))
        service.create_history_entry(user2, EventId.new(), "Volunteer", 7.0, datetime.now() - timedelta(days=2))
        
        # User 3: 5 hours total
        service.create_history_entry(user3, EventId.new(), "Volunteer", 5.0, datetime.now() - timedelta(days=1))
        
        top_volunteers = service.get_top_volunteers_by_hours(limit=3)
        
        assert len(top_volunteers) >= 1
        # Should be sorted by hours descending
        if len(top_volunteers) >= 2:
            assert top_volunteers[0][1] >= top_volunteers[1][1]  # First has more hours than second
    
    def test_get_top_volunteers_by_events(self, service):
        """Test getting top volunteers by number of events"""
        user1 = UserId.new()
        user2 = UserId.new()
        
        # User 1: 3 events
        service.create_history_entry(user1, EventId.new(), "Volunteer", 4.0, datetime.now() - timedelta(days=1))
        service.create_history_entry(user1, EventId.new(), "Volunteer", 3.0, datetime.now() - timedelta(days=2))
        service.create_history_entry(user1, EventId.new(), "Volunteer", 2.0, datetime.now() - timedelta(days=3))
        
        # User 2: 1 event
        service.create_history_entry(user2, EventId.new(), "Volunteer", 8.0, datetime.now() - timedelta(days=1))
        
        top_volunteers = service.get_top_volunteers_by_events(limit=3)
        
        assert len(top_volunteers) >= 1
        # Should be sorted by event count descending
        if len(top_volunteers) >= 2:
            assert top_volunteers[0][1] >= top_volunteers[1][1]
    
    def test_update_history_entry(self, service, sample_user_id, sample_event_id):
        """Test updating an existing history entry"""
        entry = service.create_history_entry(
            user_id=sample_user_id,
            event_id=sample_event_id,
            role="Original Role",
            hours=4.0,
            date=datetime.now() - timedelta(days=1),
            notes="Original notes"
        )
        
        updated_entry = service.update_history_entry(
            entry_id=entry.id,
            role="Updated Role",
            hours=5.5,
            notes="Updated notes"
        )
        
        assert updated_entry is not None
        assert updated_entry.role == "Updated Role"
        assert updated_entry.hours == 5.5
        assert updated_entry.notes == "Updated notes"
    
    def test_update_history_entry_not_found(self, service):
        """Test updating non-existent entry returns None"""
        fake_id = VolunteerHistoryEntryId(uuid4())
        result = service.update_history_entry(fake_id, role="Should Fail")
        assert result is None
    
    def test_delete_history_entry(self, service, sample_user_id, sample_event_id):
        """Test deleting a history entry"""
        entry = service.create_history_entry(
            user_id=sample_user_id,
            event_id=sample_event_id,
            role="To Delete",
            hours=4.0,
            date=datetime.now() - timedelta(days=1)
        )
        
        # Verify it exists
        assert service.get_history_entry_by_id(entry.id) is not None
        
        # Delete it
        success = service.delete_history_entry(entry.id)
        assert success is True
        
        # Verify it's gone
        assert service.get_history_entry_by_id(entry.id) is None
    
    def test_delete_history_entry_not_found(self, service):
        """Test deleting non-existent entry returns False"""
        fake_id = VolunteerHistoryEntryId(uuid4())
        success = service.delete_history_entry(fake_id)
        assert success is False
    
    def test_get_volunteer_statistics(self, service, sample_user_id):
        """Test getting comprehensive volunteer statistics"""
        event1_id = EventId.new()
        event2_id = EventId.new()
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event1_id,
            role="Volunteer",
            hours=4.0,
            date=datetime.now() - timedelta(days=1)
        )
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=event2_id,
            role="Team Leader",
            hours=6.0,
            date=datetime.now() - timedelta(days=5)
        )
        
        stats = service.get_volunteer_statistics(sample_user_id)
        
        assert "total_hours" in stats
        assert "total_events" in stats
        assert "unique_roles" in stats
        assert "recent_activity" in stats
        assert stats["total_hours"] == 10.0
        assert stats["total_events"] == 2
    
    def test_get_monthly_volunteer_hours(self, service, sample_user_id):
        """Test getting monthly volunteer hours for a year"""
        # Create entries in different months
        january_date = datetime(2024, 1, 15)
        february_date = datetime(2024, 2, 15)
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=EventId.new(),
            role="Volunteer",
            hours=4.0,
            date=january_date
        )
        
        service.create_history_entry(
            user_id=sample_user_id,
            event_id=EventId.new(),
            role="Volunteer",
            hours=6.0,
            date=february_date
        )
        
        monthly_hours = service.get_monthly_volunteer_hours(sample_user_id, 2024)
        
        assert isinstance(monthly_hours, dict)
        assert 1 in monthly_hours  # January
        assert 2 in monthly_hours  # February
        assert monthly_hours[1] == 4.0
        assert monthly_hours[2] == 6.0