"""
Tests for Events API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from src.main import app


class TestEventsAPI:
    """Test Events API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_event_data(self):
        """Sample event data for testing"""
        return {
            "title": "Test Event API",
            "description": "A test event via API",
            "location": {
                "name": "API Test Location",
                "address": "456 API St",
                "city": "Houston",
                "state": "TX",
                "postal_code": "77002"
            },
            "required_skills": ["python", "api-testing"],
            "starts_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "ends_at": (datetime.now() + timedelta(days=1, hours=3)).isoformat(),
            "capacity": 25
        }
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_get_all_events(self, client):
        """Test GET /api/v1/events/"""
        response = client.get("/api/v1/events/")
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)
        assert isinstance(data["total"], int)
        assert data["total"] >= 0
    
    def test_create_event(self, client, sample_event_data):
        """Test POST /api/v1/events/"""
        response = client.post("/api/v1/events/", json=sample_event_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == sample_event_data["title"]
        assert data["description"] == sample_event_data["description"]
        assert data["capacity"] == sample_event_data["capacity"]
        assert "id" in data
        assert data["status"] == "DRAFT"
    
    def test_create_event_invalid_data(self, client):
        """Test POST /api/v1/events/ with invalid data"""
        invalid_data = {
            "title": "",  # Empty title
            "description": "Test",
            "location": {
                "name": "Test Location"
            },
            "required_skills": [],
            "starts_at": (datetime.now() - timedelta(days=1)).isoformat(),  # Past date
        }
        
        response = client.post("/api/v1/events/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_event_by_id(self, client, sample_event_data):
        """Test GET /api/v1/events/{event_id}"""
        # First create an event
        create_response = client.post("/api/v1/events/", json=sample_event_data)
        assert create_response.status_code == 201
        
        event_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/events/{event_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == event_id
        assert data["title"] == sample_event_data["title"]
    
    def test_get_event_by_id_not_found(self, client):
        """Test GET /api/v1/events/{event_id} with non-existent ID"""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/v1/events/{fake_id}")
        assert response.status_code == 404
    
    def test_update_event(self, client, sample_event_data):
        """Test PUT /api/v1/events/{event_id}"""
        # First create an event
        create_response = client.post("/api/v1/events/", json=sample_event_data)
        assert create_response.status_code == 201
        
        event_id = create_response.json()["id"]
        
        # Update data
        update_data = {
            "title": "Updated Event Title",
            "description": "Updated description",
            "capacity": 50
        }
        
        # Update the event
        response = client.put(f"/api/v1/events/{event_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["capacity"] == update_data["capacity"]
    
    def test_delete_event(self, client, sample_event_data):
        """Test DELETE /api/v1/events/{event_id}"""
        # First create an event
        create_response = client.post("/api/v1/events/", json=sample_event_data)
        assert create_response.status_code == 201
        
        event_id = create_response.json()["id"]
        
        # Delete the event
        response = client.delete(f"/api/v1/events/{event_id}")
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/events/{event_id}")
        assert get_response.status_code == 404
    
    def test_search_events(self, client):
        """Test POST /api/v1/events/search"""
        search_data = {
            "skills": ["python"],
            "city": "Houston",
            "state": "TX"
        }
        
        response = client.post("/api/v1/events/search", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)
    
    def test_get_published_events(self, client):
        """Test GET /api/v1/events/published"""
        response = client.get("/api/v1/events/published")
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)
    
    def test_get_upcoming_events(self, client):
        """Test GET /api/v1/events/upcoming"""
        response = client.get("/api/v1/events/upcoming")
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)
    
    def test_publish_event(self, client, sample_event_data):
        """Test POST /api/v1/events/{event_id}/publish"""
        # Create event
        create_response = client.post("/api/v1/events/", json=sample_event_data)
        event_id = create_response.json()["id"]
        
        # Publish it
        response = client.post(f"/api/v1/events/{event_id}/publish")
        assert response.status_code == 200
        
        # Verify it's published
        get_response = client.get(f"/api/v1/events/{event_id}")
        assert get_response.json()["status"] == "PUBLISHED"
    
    def test_publish_event_not_found(self, client):
        """Test publishing non-existent event"""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.post(f"/api/v1/events/{fake_id}/publish")
        assert response.status_code == 404
    
    def test_cancel_event(self, client, sample_event_data):
        """Test POST /api/v1/events/{event_id}/cancel"""
        # Create and publish event
        create_response = client.post("/api/v1/events/", json=sample_event_data)
        event_id = create_response.json()["id"]
        client.post(f"/api/v1/events/{event_id}/publish")
        
        # Cancel it
        response = client.post(f"/api/v1/events/{event_id}/cancel")
        assert response.status_code == 200
        
        # Verify it's cancelled
        get_response = client.get(f"/api/v1/events/{event_id}")
        assert get_response.json()["status"] == "CANCELLED"
    
    def test_cancel_event_not_found(self, client):
        """Test canceling non-existent event"""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.post(f"/api/v1/events/{fake_id}/cancel")
        assert response.status_code == 404
    
    def test_search_events_by_location(self, client):
        """Test searching events by location"""
        search_data = {
            "city": "Houston",
            "state": "TX"
        }
        
        response = client.post("/api/v1/events/search", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert "total" in data
    
    def test_search_events_by_date_range(self, client):
        """Test searching events by date range"""
        search_data = {
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/events/search", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert "total" in data
    
    def test_search_events_empty_criteria(self, client):
        """Test searching events with empty criteria"""
        search_data = {}
        
        response = client.post("/api/v1/events/search", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert "total" in data
    
    def test_create_event_without_location(self, client):
        """Test creating event without location"""
        event_data = {
            "title": "No Location Event",
            "description": "Event without location",
            "required_skills": ["remote"],
            "starts_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "ends_at": (datetime.now() + timedelta(days=1, hours=2)).isoformat()
        }
        
        response = client.post("/api/v1/events/", json=event_data)
        assert response.status_code == 422  # Should require location
    
    def test_create_event_without_end_time(self, client):
        """Test creating event without end time"""
        event_data = {
            "title": "Open Ended Event",
            "description": "Event without end time",
            "location": {
                "name": "Test Location",
                "address": "123 Test St",
                "city": "Houston",
                "state": "TX",
                "postal_code": "77001"
            },
            "required_skills": ["flexible"],
            "starts_at": (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        response = client.post("/api/v1/events/", json=event_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["ends_at"] is None
    
    def test_update_event_partial(self, client, sample_event_data):
        """Test partial update of event"""
        # Create event
        create_response = client.post("/api/v1/events/", json=sample_event_data)
        event_id = create_response.json()["id"]
        
        # Update only title
        update_data = {"title": "Partially Updated Event"}
        
        response = client.put(f"/api/v1/events/{event_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Partially Updated Event"
        # Other fields should remain unchanged
        assert data["description"] == sample_event_data["description"]
    
    def test_update_event_invalid_dates(self, client, sample_event_data):
        """Test updating event with invalid dates"""
        # Create event
        create_response = client.post("/api/v1/events/", json=sample_event_data)
        event_id = create_response.json()["id"]
        
        # Try to update with past start date
        update_data = {
            "starts_at": (datetime.now() - timedelta(days=1)).isoformat()
        }
        
        response = client.put(f"/api/v1/events/{event_id}", json=update_data)
        assert response.status_code == 422  # Should fail validation
    
    def test_get_all_events_pagination(self, client):
        """Test getting events with pagination parameters"""
        response = client.get("/api/v1/events/?limit=5&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert len(data["events"]) <= 5
    
    def test_create_event_long_title(self, client, sample_event_data):
        """Test creating event with overly long title"""
        sample_event_data["title"] = "x" * 101  # Assuming 100 char limit
        
        response = client.post("/api/v1/events/", json=sample_event_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_event_long_description(self, client, sample_event_data):
        """Test creating event with overly long description"""
        sample_event_data["description"] = "x" * 501  # Assuming 500 char limit
        
        response = client.post("/api/v1/events/", json=sample_event_data)
        assert response.status_code == 422  # Validation error