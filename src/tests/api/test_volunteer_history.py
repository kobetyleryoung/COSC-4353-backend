"""
Tests for Volunteer History API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from uuid import uuid4

from src.main import app


class TestVolunteerHistoryAPI:
    """Test Volunteer History API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return str(uuid4())
    
    @pytest.fixture
    def sample_event_id(self):
        """Sample event ID for testing"""
        return str(uuid4())
    
    @pytest.fixture
    def sample_history_data(self, sample_user_id, sample_event_id):
        """Sample history entry data for testing"""
        return {
            "user_id": sample_user_id,
            "event_id": sample_event_id,
            "role": "General Volunteer",
            "hours": 4.5,
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "notes": "Great experience helping at the event"
        }
    
    def test_get_recent_history(self, client):
        """Test GET /api/v1/volunteer-history/"""
        response = client.get("/api/v1/volunteer-history/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should return list of history entries (may be empty or have sample data)
        for entry in data:
            assert "id" in entry
            assert "user_id" in entry
            assert "event_id" in entry
            assert "role" in entry
            assert "hours" in entry
            assert "date" in entry
    
    def test_get_recent_history_with_days_filter(self, client):
        """Test GET /api/v1/volunteer-history/ with days parameter"""
        response = client.get("/api/v1/volunteer-history/?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_history_entry(self, client, sample_history_data):
        """Test POST /api/v1/volunteer-history/"""
        response = client.post("/api/v1/volunteer-history/", json=sample_history_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["user_id"] == sample_history_data["user_id"]
        assert data["event_id"] == sample_history_data["event_id"]
        assert data["role"] == sample_history_data["role"]
        assert data["hours"] == sample_history_data["hours"]
        assert data["notes"] == sample_history_data["notes"]
        assert "id" in data
        assert "date" in data
    
    def test_create_history_entry_minimal(self, client, sample_user_id, sample_event_id):
        """Test creating history entry with minimal data"""
        minimal_data = {
            "user_id": sample_user_id,
            "event_id": sample_event_id,
            "role": "Volunteer",
            "hours": 3.0,
            "date": (datetime.now() - timedelta(days=1)).isoformat()
        }
        
        response = client.post("/api/v1/volunteer-history/", json=minimal_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["notes"] is None
        assert data["hours"] == 3.0
    
    def test_create_history_entry_invalid_data(self, client):
        """Test POST /api/v1/volunteer-history/ with invalid data"""
        invalid_data = {
            "user_id": str(uuid4()),
            "event_id": str(uuid4()),
            "role": "",  # Empty role
            "hours": -1.0,  # Negative hours
            "date": (datetime.now() + timedelta(days=1)).isoformat()  # Future date
        }
        
        response = client.post("/api/v1/volunteer-history/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_history_entry_by_id(self, client, sample_history_data):
        """Test GET /api/v1/volunteer-history/{entry_id}"""
        # First create an entry
        create_response = client.post("/api/v1/volunteer-history/", json=sample_history_data)
        assert create_response.status_code == 201
        
        entry_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/volunteer-history/{entry_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == entry_id
        assert data["role"] == sample_history_data["role"]
    
    def test_get_history_entry_by_id_not_found(self, client):
        """Test GET /api/v1/volunteer-history/{entry_id} with non-existent ID"""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/volunteer-history/{fake_id}")
        assert response.status_code == 404
    
    def test_get_user_history(self, client, sample_history_data):
        """Test GET /api/v1/volunteer-history/user/{user_id}"""
        # Create history entry
        client.post("/api/v1/volunteer-history/", json=sample_history_data)
        user_id = sample_history_data["user_id"]
        
        response = client.get(f"/api/v1/volunteer-history/user/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert isinstance(data["entries"], list)
        assert isinstance(data["total"], int)
        
        # Should find our entry
        found_entry = any(
            entry["user_id"] == user_id
            for entry in data["entries"]
        )
        assert found_entry
    
    def test_get_event_history(self, client, sample_history_data):
        """Test GET /api/v1/volunteer-history/event/{event_id}"""
        # Create history entry
        client.post("/api/v1/volunteer-history/", json=sample_history_data)
        event_id = sample_history_data["event_id"]
        
        response = client.get(f"/api/v1/volunteer-history/event/{event_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert isinstance(data["entries"], list)
        
        # Should find our entry
        found_entry = any(
            entry["event_id"] == event_id
            for entry in data["entries"]
        )
        assert found_entry
    
    def test_update_history_entry(self, client, sample_history_data):
        """Test PUT /api/v1/volunteer-history/{entry_id}"""
        # Create entry
        create_response = client.post("/api/v1/volunteer-history/", json=sample_history_data)
        entry_id = create_response.json()["id"]
        
        # Update data
        update_data = {
            "role": "Team Leader",
            "hours": 6.0,
            "notes": "Updated notes"
        }
        
        response = client.put(f"/api/v1/volunteer-history/{entry_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["role"] == update_data["role"]
        assert data["hours"] == update_data["hours"]
        assert data["notes"] == update_data["notes"]
    
    def test_update_history_entry_not_found(self, client):
        """Test PUT /api/v1/volunteer-history/{entry_id} with non-existent ID"""
        fake_id = str(uuid4())
        update_data = {"role": "Should Fail"}
        
        response = client.put(f"/api/v1/volunteer-history/{fake_id}", json=update_data)
        assert response.status_code == 404
    
    def test_delete_history_entry(self, client, sample_history_data):
        """Test DELETE /api/v1/volunteer-history/{entry_id}"""
        # Create entry
        create_response = client.post("/api/v1/volunteer-history/", json=sample_history_data)
        entry_id = create_response.json()["id"]
        
        # Delete entry
        response = client.delete(f"/api/v1/volunteer-history/{entry_id}")
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/volunteer-history/{entry_id}")
        assert get_response.status_code == 404
    
    def test_delete_history_entry_not_found(self, client):
        """Test deleting non-existent entry"""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/volunteer-history/{fake_id}")
        assert response.status_code == 404
    
    def test_get_user_total_hours(self, client, sample_user_id):
        """Test GET /api/v1/volunteer-history/user/{user_id}/total-hours"""
        response = client.get(f"/api/v1/volunteer-history/user/{sample_user_id}/total-hours")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "total_hours" in data
        assert isinstance(data["total_hours"], (int, float))
    
    def test_get_user_hours_in_period(self, client, sample_user_id):
        """Test GET /api/v1/volunteer-history/user/{user_id}/hours-in-period"""
        start_date = (datetime.now() - timedelta(days=30)).isoformat()[:10]  # YYYY-MM-DD
        end_date = datetime.now().isoformat()[:10]
        
        response = client.get(
            f"/api/v1/volunteer-history/user/{sample_user_id}/hours-in-period"
            f"?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "hours" in data
        assert "start_date" in data
        assert "end_date" in data
    
    def test_get_user_hours_in_period_invalid_dates(self, client, sample_user_id):
        """Test hours in period with invalid date format"""
        response = client.get(
            f"/api/v1/volunteer-history/user/{sample_user_id}/hours-in-period"
            f"?start_date=invalid&end_date=invalid"
        )
        assert response.status_code == 422  # Validation error
    
    def test_get_user_event_count(self, client, sample_user_id):
        """Test GET /api/v1/volunteer-history/user/{user_id}/event-count"""
        response = client.get(f"/api/v1/volunteer-history/user/{sample_user_id}/event-count")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "event_count" in data
        assert isinstance(data["event_count"], int)
    
    def test_get_user_roles(self, client, sample_user_id):
        """Test GET /api/v1/volunteer-history/user/{user_id}/roles"""
        response = client.get(f"/api/v1/volunteer-history/user/{sample_user_id}/roles")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "roles" in data
        assert isinstance(data["roles"], list)
    
    def test_get_user_statistics(self, client, sample_user_id):
        """Test GET /api/v1/volunteer-history/user/{user_id}/statistics"""
        response = client.get(f"/api/v1/volunteer-history/user/{sample_user_id}/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "total_hours" in data
        assert "total_events" in data
        assert "unique_roles" in data
        assert "recent_activity" in data
    
    def test_get_user_monthly_hours(self, client, sample_user_id):
        """Test GET /api/v1/volunteer-history/user/{user_id}/monthly-hours/{year}"""
        year = datetime.now().year
        
        response = client.get(f"/api/v1/volunteer-history/user/{sample_user_id}/monthly-hours/{year}")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "year" in data
        assert "monthly_hours" in data
        assert isinstance(data["monthly_hours"], dict)
        assert data["year"] == year
    
    def test_get_top_volunteers_by_hours(self, client):
        """Test GET /api/v1/volunteer-history/top-volunteers/by-hours"""
        response = client.get("/api/v1/volunteer-history/top-volunteers/by-hours")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check structure of top volunteer entries
        for volunteer in data:
            assert "user_id" in volunteer
            assert "total_hours" in volunteer
            assert "rank" in volunteer
    
    def test_get_top_volunteers_by_hours_with_limit(self, client):
        """Test GET /api/v1/volunteer-history/top-volunteers/by-hours with limit"""
        response = client.get("/api/v1/volunteer-history/top-volunteers/by-hours?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_top_volunteers_by_events(self, client):
        """Test GET /api/v1/volunteer-history/top-volunteers/by-events"""
        response = client.get("/api/v1/volunteer-history/top-volunteers/by-events")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check structure of top volunteer entries
        for volunteer in data:
            assert "user_id" in volunteer
            assert "event_count" in volunteer
            assert "rank" in volunteer
    
    def test_get_top_volunteers_by_events_with_limit(self, client):
        """Test GET /api/v1/volunteer-history/top-volunteers/by-events with limit"""
        response = client.get("/api/v1/volunteer-history/top-volunteers/by-events?limit=3")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3