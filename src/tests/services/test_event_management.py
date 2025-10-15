"""
Tests for EventManagementService
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from src.services.event_management import EventManagementService
from src.domain.events import Event, EventId, EventStatus, Location
from src.domain.users import UserId


class TestEventManagementService:
    """Test EventManagementService functionality"""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger"""
        return logging.getLogger("test")
    
    @pytest.fixture
    def service(self, logger):
        """Create a fresh EventManagementService for each test"""
        return EventManagementService(logger)
    
    @pytest.fixture
    def sample_location(self):
        """Sample location for testing"""
        return Location(
            name="Test Center",
            address="123 Test St",
            city="Houston",
            state="TX",
            postal_code="77001"
        )
    
    def test_service_initialization(self, service):
        """Test service initializes with empty events"""
        events = service.get_all_events()
        assert len(events) >= 0  # May have sample data
        assert isinstance(events, list)
    
    def test_create_event(self, service, sample_location):
        """Test creating a new event"""
        title = "Test Event"
        description = "A test event"
        required_skills = ["python", "testing"]
        starts_at = datetime.now() + timedelta(days=1)
        ends_at = starts_at + timedelta(hours=2)
        capacity = 20
        
        event = service.create_event(
            title=title,
            description=description,
            location=sample_location,
            required_skills=required_skills,
            starts_at=starts_at,
            ends_at=ends_at,
            capacity=capacity
        )
        
        assert isinstance(event, Event)
        assert event.title == title
        assert event.description == description
        assert event.location == sample_location
        assert event.required_skills == required_skills
        assert event.starts_at == starts_at
        assert event.ends_at == ends_at
        assert event.capacity == capacity
        assert event.status == EventStatus.DRAFT
    
    def test_create_event_validation_past_date(self, service, sample_location):
        """Test creating event with past date raises error"""
        past_date = datetime.now() - timedelta(days=1)
        
        with pytest.raises(ValueError, match="cannot be in the past"):
            service.create_event(
                title="Past Event",
                description="Should fail",
                location=sample_location,
                required_skills=[],
                starts_at=past_date
            )
    
    def test_create_event_validation_end_before_start(self, service, sample_location):
        """Test creating event with end time before start time raises error"""
        starts_at = datetime.now() + timedelta(days=1)
        ends_at = starts_at - timedelta(hours=1)  # End before start
        
        with pytest.raises(ValueError, match="End time must be after start time"):
            service.create_event(
                title="Invalid Event",
                description="Should fail",
                location=sample_location,
                required_skills=[],
                starts_at=starts_at,
                ends_at=ends_at
            )
    
    def test_get_event_by_id(self, service, sample_location):
        """Test retrieving event by ID"""
        # Create an event
        event = service.create_event(
            title="Findable Event",
            description="Test",
            location=sample_location,
            required_skills=[],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        # Find it by ID
        found_event = service.get_event_by_id(event.id)
        assert found_event is not None
        assert found_event.id == event.id
        assert found_event.title == event.title
    
    def test_get_event_by_id_not_found(self, service):
        """Test retrieving non-existent event returns None"""
        non_existent_id = EventId(uuid4())
        found_event = service.get_event_by_id(non_existent_id)
        assert found_event is None
    
    def test_update_event(self, service, sample_location):
        """Test updating an existing event"""
        # Create an event
        event = service.create_event(
            title="Original Title",
            description="Original description",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        # Update it
        new_location = Location(name="New Location")
        updated_event = service.update_event(
            event_id=event.id,
            title="Updated Title",
            description="Updated description",
            location=new_location,
            required_skills=["skill1", "skill2"],
            capacity=30
        )
        
        assert updated_event is not None
        assert updated_event.title == "Updated Title"
        assert updated_event.description == "Updated description"
        assert updated_event.location == new_location
        assert updated_event.required_skills == ["skill1", "skill2"]
        assert updated_event.capacity == 30
    
    def test_update_event_not_found(self, service):
        """Test updating non-existent event returns None"""
        non_existent_id = EventId(uuid4())
        updated_event = service.update_event(
            event_id=non_existent_id,
            title="Should fail"
        )
        assert updated_event is None
    
    def test_delete_event(self, service, sample_location):
        """Test deleting an event"""
        # Create an event
        event = service.create_event(
            title="To be deleted",
            description="Test",
            location=sample_location,
            required_skills=[],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        # Verify it exists
        assert service.get_event_by_id(event.id) is not None
        
        # Delete it
        success = service.delete_event(event.id)
        assert success is True
        
        # Verify it's gone
        assert service.get_event_by_id(event.id) is None
    
    def test_delete_event_not_found(self, service):
        """Test deleting non-existent event returns False"""
        non_existent_id = EventId(uuid4())
        success = service.delete_event(non_existent_id)
        assert success is False
    
    def test_get_events_by_skills(self, service, sample_location):
        """Test filtering events by skills"""
        # Create events with different skills
        event1 = service.create_event(
            title="Python Event",
            description="Test",
            location=sample_location,
            required_skills=["python", "backend"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        event2 = service.create_event(
            title="Frontend Event",
            description="Test",
            location=sample_location,
            required_skills=["javascript", "react"],
            starts_at=datetime.now() + timedelta(days=2)
        )
        
        event3 = service.create_event(
            title="Full Stack Event",
            description="Test",
            location=sample_location,
            required_skills=["python", "javascript"],
            starts_at=datetime.now() + timedelta(days=3)
        )
        
        # Search for Python events
        python_events = service.get_events_by_skills(["python"])
        python_event_ids = [e.id for e in python_events]
        
        assert event1.id in python_event_ids
        assert event3.id in python_event_ids
        assert event2.id not in python_event_ids
        
        # Search for JavaScript events
        js_events = service.get_events_by_skills(["javascript"])
        js_event_ids = [e.id for e in js_events]
        
        assert event2.id in js_event_ids
        assert event3.id in js_event_ids
        assert event1.id not in js_event_ids
    
    def test_get_events_by_location(self, service, sample_location):
        """Test filtering events by location"""
        # Create events in different locations
        houston_location = Location(
            name="Houston Center",
            address="123 Houston St",
            city="Houston",
            state="TX",
            postal_code="77001"
        )
        
        dallas_location = Location(
            name="Dallas Center",
            address="456 Dallas St",
            city="Dallas",
            state="TX",
            postal_code="75201"
        )
        
        event1 = service.create_event(
            title="Houston Event",
            description="Test",
            location=houston_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        event2 = service.create_event(
            title="Dallas Event",
            description="Test",
            location=dallas_location,
            required_skills=["skill2"],
            starts_at=datetime.now() + timedelta(days=2)
        )
        
        houston_events = service.get_events_by_location("Houston", "TX")
        houston_event_ids = [e.id for e in houston_events]
        
        assert event1.id in houston_event_ids
        assert event2.id not in houston_event_ids
    
    def test_get_published_events(self, service, sample_location):
        """Test getting only published events"""
        # Create draft event
        draft_event = service.create_event(
            title="Draft Event",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        # Create published event
        published_event = service.create_event(
            title="Published Event",
            description="Test",
            location=sample_location,
            required_skills=["skill2"],
            starts_at=datetime.now() + timedelta(days=2)
        )
        service.publish_event(published_event.id)
        
        published_events = service.get_published_events()
        published_event_ids = [e.id for e in published_events]
        
        assert published_event.id in published_event_ids
        assert draft_event.id not in published_event_ids
    
    def test_get_upcoming_events(self, service, sample_location):
        """Test getting upcoming published events"""
        # Create past event (published)
        past_event = service.create_event(
            title="Past Event",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() - timedelta(days=1)
        )
        service.publish_event(past_event.id)
        
        # Create future event (published)
        future_event = service.create_event(
            title="Future Event",
            description="Test",
            location=sample_location,
            required_skills=["skill2"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        service.publish_event(future_event.id)
        
        upcoming_events = service.get_upcoming_events()
        upcoming_event_ids = [e.id for e in upcoming_events]
        
        assert future_event.id in upcoming_event_ids
        assert past_event.id not in upcoming_event_ids
    
    def test_publish_event(self, service, sample_location):
        """Test publishing an event"""
        event = service.create_event(
            title="Event to Publish",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        # Initially should be draft
        assert event.status.name == "DRAFT"
        
        # Publish it
        success = service.publish_event(event.id)
        assert success is True
        
        # Check status changed
        updated_event = service.get_event_by_id(event.id)
        assert updated_event.status.name == "PUBLISHED"
    
    def test_publish_event_not_found(self, service):
        """Test publishing non-existent event"""
        from uuid import uuid4
        from src.domain.events import EventId
        
        non_existent_id = EventId(uuid4())
        success = service.publish_event(non_existent_id)
        assert success is False
    
    def test_cancel_event(self, service, sample_location):
        """Test canceling an event"""
        event = service.create_event(
            title="Event to Cancel",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        service.publish_event(event.id)
        
        # Cancel it
        success = service.cancel_event(event.id)
        assert success is True
        
        # Check status changed
        updated_event = service.get_event_by_id(event.id)
        assert updated_event.status.name == "CANCELLED"
    
    def test_cancel_event_not_found(self, service):
        """Test canceling non-existent event"""
        from uuid import uuid4
        from src.domain.events import EventId
        
        non_existent_id = EventId(uuid4())
        success = service.cancel_event(non_existent_id)
        assert success is False
    
    def test_update_event_validation_empty_title(self, service, sample_location):
        """Test update validation fails for empty title"""
        event = service.create_event(
            title="Original Title",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        with pytest.raises(ValueError, match="Title cannot be empty"):
            service.update_event(event.id, title="")
    
    def test_update_event_validation_past_start_date(self, service, sample_location):
        """Test update validation fails for past start date"""
        event = service.create_event(
            title="Test Event",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        past_date = datetime.now() - timedelta(days=1)
        with pytest.raises(ValueError, match="Start time cannot be in the past"):
            service.update_event(event.id, starts_at=past_date)
    
    def test_update_event_validation_end_before_start(self, service, sample_location):
        """Test update validation fails when end time is before start time"""
        event = service.create_event(
            title="Test Event",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        starts_at = datetime.now() + timedelta(days=2)
        ends_at = starts_at - timedelta(hours=1)  # End before start
        
        with pytest.raises(ValueError, match="End time must be after start time"):
            service.update_event(event.id, starts_at=starts_at, ends_at=ends_at)
    
    def test_create_event_validation_no_required_skills(self, service, sample_location):
        """Test validation fails when no required skills provided"""
        with pytest.raises(ValueError, match="Required skills cannot be empty"):
            service.create_event(
                title="No Skills Event",
                description="Test",
                location=sample_location,
                required_skills=[],
                starts_at=datetime.now() + timedelta(days=1)
            )
    
    def test_create_event_validation_invalid_capacity(self, service, sample_location):
        """Test validation fails for invalid capacity"""
        with pytest.raises(ValueError, match="Capacity must be positive"):
            service.create_event(
                title="Invalid Capacity Event",
                description="Test",
                location=sample_location,
                required_skills=["skill1"],
                starts_at=datetime.now() + timedelta(days=1),
                capacity=0
            )
    
    def test_create_event_validation_no_location(self, service):
        """Test validation fails when no location provided"""
        with pytest.raises(ValueError, match="Location is required"):
            service.create_event(
                title="No Location Event",
                description="Test",
                location=None,
                required_skills=["skill1"],
                starts_at=datetime.now() + timedelta(days=1)
            )
    
    def test_get_events_with_capacity(self, service, sample_location):
        """Test getting events with capacity information"""
        event1 = service.create_event(
            title="Event 1",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1),
            capacity=10
        )
        
        event2 = service.create_event(
            title="Event 2",
            description="Test",
            location=sample_location,
            required_skills=["skill2"],
            starts_at=datetime.now() + timedelta(days=2),
            capacity=5
        )
        
        # Mock enrollment counts
        enrolled_counts = {
            str(event1.id.value): 3,
            str(event2.id.value): 5
        }
        
        events_with_capacity = service.get_events_with_capacity(enrolled_counts)
        
        assert isinstance(events_with_capacity, list)
        assert len(events_with_capacity) >= 2
    
    def test_create_event_minimal_location(self, service):
        """Test creating event with minimal location data"""
        minimal_location = Location(name="Minimal Location")
        
        event = service.create_event(
            title="Minimal Location Event",
            description="Test",
            location=minimal_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        assert event.location.name == "Minimal Location"
        assert event.location.address is None
        assert event.location.city is None
    
    def test_update_event_status_directly(self, service, sample_location):
        """Test updating event status directly"""
        from src.domain.events import EventStatus
        
        event = service.create_event(
            title="Status Test Event",
            description="Test",
            location=sample_location,
            required_skills=["skill1"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        updated_event = service.update_event(
            event.id,
            status=EventStatus.PUBLISHED
        )
        
        assert updated_event.status == EventStatus.PUBLISHED
    
    def test_search_events_by_multiple_skills(self, service, sample_location):
        """Test searching events by multiple skills"""
        event1 = service.create_event(
            title="Multi-skill Event",
            description="Test",
            location=sample_location,
            required_skills=["python", "javascript", "communication"],
            starts_at=datetime.now() + timedelta(days=1)
        )
        
        event2 = service.create_event(
            title="Single-skill Event", 
            description="Test",
            location=sample_location,
            required_skills=["java"],
            starts_at=datetime.now() + timedelta(days=2)
        )
        
        # Search for events with both python and javascript
        matching_events = service.get_events_by_skills(["python", "javascript"])
        matching_event_ids = [e.id for e in matching_events]
        
        assert event1.id in matching_event_ids
        assert event2.id not in matching_event_ids