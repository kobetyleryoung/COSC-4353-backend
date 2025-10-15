"""
Tests for Volunteer Matching API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from uuid import uuid4

from src.main import app


class TestVolunteerMatchingAPI:
    """Test Volunteer Matching API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_event_id(self):
        """Sample event ID for testing"""
        return str(uuid4())
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return str(uuid4())
    
    @pytest.fixture
    def sample_opportunity_data(self, sample_event_id):
        """Sample opportunity data for testing"""
        return {
            "event_id": sample_event_id,
            "title": "Test Volunteer Opportunity",
            "description": "A great opportunity to help the community",
            "required_skills": ["Communication", "Organization"],
            "min_hours": 4.0,
            "max_slots": 10
        }
    
    @pytest.fixture
    def sample_match_request_data(self, sample_user_id, sample_opportunity_data, client):
        """Sample match request data with created opportunity"""
        # Create opportunity first
        opp_response = client.post("/api/v1/volunteer-matching/opportunities", json=sample_opportunity_data)
        opportunity_id = opp_response.json()["id"]
        
        return {
            "user_id": sample_user_id,
            "opportunity_id": opportunity_id
        }
    
    def test_get_all_opportunities(self, client):
        """Test GET /api/v1/volunteer-matching/opportunities"""
        response = client.get("/api/v1/volunteer-matching/opportunities")
        assert response.status_code == 200
        
        data = response.json()
        assert "opportunities" in data
        assert "total" in data
        assert isinstance(data["opportunities"], list)
        assert isinstance(data["total"], int)
    
    def test_create_opportunity(self, client, sample_opportunity_data):
        """Test POST /api/v1/volunteer-matching/opportunities"""
        response = client.post("/api/v1/volunteer-matching/opportunities", json=sample_opportunity_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["event_id"] == sample_opportunity_data["event_id"]
        assert data["title"] == sample_opportunity_data["title"]
        assert data["description"] == sample_opportunity_data["description"]
        assert data["required_skills"] == sample_opportunity_data["required_skills"]
        assert data["min_hours"] == sample_opportunity_data["min_hours"]
        assert data["max_slots"] == sample_opportunity_data["max_slots"]
        assert "id" in data
    
    def test_create_opportunity_minimal(self, client, sample_event_id):
        """Test creating opportunity with minimal data"""
        minimal_data = {
            "event_id": sample_event_id,
            "title": "Minimal Opportunity"
        }
        
        response = client.post("/api/v1/volunteer-matching/opportunities", json=minimal_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == "Minimal Opportunity"
        assert data["description"] is None
        assert data["required_skills"] == []
        assert data["min_hours"] is None
        assert data["max_slots"] is None
    
    def test_create_opportunity_invalid_data(self, client):
        """Test POST /api/v1/volunteer-matching/opportunities with invalid data"""
        invalid_data = {
            "event_id": str(uuid4()),
            "title": "",  # Empty title
            "min_hours": -1.0,  # Negative hours
            "max_slots": -1  # Negative slots
        }
        
        response = client.post("/api/v1/volunteer-matching/opportunities", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_opportunity_by_id(self, client, sample_opportunity_data):
        """Test GET /api/v1/volunteer-matching/opportunities/{opportunity_id}"""
        # Create opportunity
        create_response = client.post("/api/v1/volunteer-matching/opportunities", json=sample_opportunity_data)
        opportunity_id = create_response.json()["id"]
        
        # Retrieve it
        response = client.get(f"/api/v1/volunteer-matching/opportunities/{opportunity_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == opportunity_id
        assert data["title"] == sample_opportunity_data["title"]
    
    def test_get_opportunity_by_id_not_found(self, client):
        """Test GET /api/v1/volunteer-matching/opportunities/{opportunity_id} with non-existent ID"""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/volunteer-matching/opportunities/{fake_id}")
        assert response.status_code == 404
    
    def test_get_opportunities_by_event(self, client, sample_opportunity_data):
        """Test GET /api/v1/volunteer-matching/opportunities/event/{event_id}"""
        # Create opportunity
        client.post("/api/v1/volunteer-matching/opportunities", json=sample_opportunity_data)
        event_id = sample_opportunity_data["event_id"]
        
        response = client.get(f"/api/v1/volunteer-matching/opportunities/event/{event_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "opportunities" in data
        assert "total" in data
        assert isinstance(data["opportunities"], list)
        
        # Should find our opportunity
        found_opportunity = any(
            opp["event_id"] == event_id
            for opp in data["opportunities"]
        )
        assert found_opportunity
    
    def test_create_match_request(self, client, sample_match_request_data):
        """Test POST /api/v1/volunteer-matching/requests"""
        response = client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["user_id"] == sample_match_request_data["user_id"]
        assert data["opportunity_id"] == sample_match_request_data["opportunity_id"]
        assert data["status"] == "PENDING"
        assert "id" in data
        assert "requested_at" in data
    
    def test_create_match_request_duplicate(self, client, sample_match_request_data):
        """Test creating duplicate match request"""
        # Create first request
        client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        
        # Try to create duplicate
        response = client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        assert response.status_code == 422  # Should fail validation
    
    def test_create_match_request_invalid_opportunity(self, client, sample_user_id):
        """Test creating match request for non-existent opportunity"""
        invalid_data = {
            "user_id": sample_user_id,
            "opportunity_id": str(uuid4())  # Non-existent opportunity
        }
        
        response = client.post("/api/v1/volunteer-matching/requests", json=invalid_data)
        assert response.status_code == 422  # Should fail validation
    
    def test_get_match_requests_by_opportunity(self, client, sample_match_request_data):
        """Test GET /api/v1/volunteer-matching/requests/opportunity/{opportunity_id}"""
        # Create match request
        client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        opportunity_id = sample_match_request_data["opportunity_id"]
        
        response = client.get(f"/api/v1/volunteer-matching/requests/opportunity/{opportunity_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "requests" in data
        assert "total" in data
        assert isinstance(data["requests"], list)
        
        # Should find our request
        found_request = any(
            req["opportunity_id"] == opportunity_id
            for req in data["requests"]
        )
        assert found_request
    
    def test_get_match_requests_by_user(self, client, sample_match_request_data):
        """Test GET /api/v1/volunteer-matching/requests/user/{user_id}"""
        # Create match request
        client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        user_id = sample_match_request_data["user_id"]
        
        response = client.get(f"/api/v1/volunteer-matching/requests/user/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "requests" in data
        assert "total" in data
        assert isinstance(data["requests"], list)
        
        # Should find our request
        found_request = any(
            req["user_id"] == user_id
            for req in data["requests"]
        )
        assert found_request
    
    def test_approve_match_request(self, client, sample_match_request_data):
        """Test POST /api/v1/volunteer-matching/requests/{request_id}/approve"""
        # Create match request
        create_response = client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        request_id = create_response.json()["id"]
        
        # Approve it
        response = client.post(f"/api/v1/volunteer-matching/requests/{request_id}/approve")
        assert response.status_code == 200
        
        data = response.json()
        assert "match" in data
        assert data["match"]["user_id"] == sample_match_request_data["user_id"]
        assert data["match"]["opportunity_id"] == sample_match_request_data["opportunity_id"]
        assert data["match"]["status"] == "ACCEPTED"
    
    def test_approve_match_request_not_found(self, client):
        """Test approving non-existent match request"""
        fake_id = str(uuid4())
        response = client.post(f"/api/v1/volunteer-matching/requests/{fake_id}/approve")
        assert response.status_code == 404
    
    def test_reject_match_request(self, client, sample_match_request_data):
        """Test POST /api/v1/volunteer-matching/requests/{request_id}/reject"""
        # Create match request
        create_response = client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        request_id = create_response.json()["id"]
        
        # Reject it
        reject_data = {"reason": "Position filled"}
        response = client.post(f"/api/v1/volunteer-matching/requests/{request_id}/reject", json=reject_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_reject_match_request_not_found(self, client):
        """Test rejecting non-existent match request"""
        fake_id = str(uuid4())
        response = client.post(f"/api/v1/volunteer-matching/requests/{fake_id}/reject")
        assert response.status_code == 404
    
    def test_get_matches_by_user(self, client, sample_match_request_data):
        """Test GET /api/v1/volunteer-matching/matches/user/{user_id}"""
        # Create and approve match request
        create_response = client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        request_id = create_response.json()["id"]
        client.post(f"/api/v1/volunteer-matching/requests/{request_id}/approve")
        
        user_id = sample_match_request_data["user_id"]
        
        response = client.get(f"/api/v1/volunteer-matching/matches/user/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "matches" in data
        assert "total" in data
        assert isinstance(data["matches"], list)
    
    def test_get_matches_by_opportunity(self, client, sample_match_request_data):
        """Test GET /api/v1/volunteer-matching/matches/opportunity/{opportunity_id}"""
        # Create and approve match request
        create_response = client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        request_id = create_response.json()["id"]
        client.post(f"/api/v1/volunteer-matching/requests/{request_id}/approve")
        
        opportunity_id = sample_match_request_data["opportunity_id"]
        
        response = client.get(f"/api/v1/volunteer-matching/matches/opportunity/{opportunity_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "matches" in data
        assert "total" in data
        assert isinstance(data["matches"], list)
    
    def test_cancel_match(self, client, sample_match_request_data):
        """Test POST /api/v1/volunteer-matching/matches/{match_id}/cancel"""
        # Create and approve match request
        create_response = client.post("/api/v1/volunteer-matching/requests", json=sample_match_request_data)
        request_id = create_response.json()["id"]
        approve_response = client.post(f"/api/v1/volunteer-matching/requests/{request_id}/approve")
        match_id = approve_response.json()["match"]["id"]
        
        # Cancel the match
        response = client.post(f"/api/v1/volunteer-matching/matches/{match_id}/cancel")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_cancel_match_not_found(self, client):
        """Test canceling non-existent match"""
        fake_id = str(uuid4())
        response = client.post(f"/api/v1/volunteer-matching/matches/{fake_id}/cancel")
        assert response.status_code == 404
    
    def test_find_matching_volunteers(self, client, sample_opportunity_data):
        """Test POST /api/v1/volunteer-matching/find-volunteers"""
        # Create opportunity
        create_response = client.post("/api/v1/volunteer-matching/opportunities", json=sample_opportunity_data)
        opportunity_id = create_response.json()["id"]
        
        # Mock profile data for matching
        search_data = {
            "opportunity_id": opportunity_id,
            "profiles": [
                {
                    "user_id": str(uuid4()),
                    "display_name": "Test User",
                    "skills": ["Communication", "Organization"],
                    "tags": ["experienced"],
                    "availability": []
                }
            ],
            "min_score": 0.5
        }
        
        response = client.post("/api/v1/volunteer-matching/find-volunteers", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "matches" in data
        assert "total" in data
        assert isinstance(data["matches"], list)
    
    def test_find_matching_opportunities(self, client, sample_user_id):
        """Test POST /api/v1/volunteer-matching/find-opportunities"""
        # Mock user profile for opportunity matching
        search_data = {
            "user_id": sample_user_id,
            "profile": {
                "user_id": sample_user_id,
                "display_name": "Test User",
                "skills": ["Python", "Communication"],
                "tags": ["experienced"],
                "availability": []
            },
            "min_score": 0.3
        }
        
        response = client.post("/api/v1/volunteer-matching/find-opportunities", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "matches" in data
        assert "total" in data
        assert isinstance(data["matches"], list)
    
    def test_calculate_match_score(self, client, sample_opportunity_data, sample_user_id):
        """Test POST /api/v1/volunteer-matching/calculate-score"""
        # Create opportunity
        create_response = client.post("/api/v1/volunteer-matching/opportunities", json=sample_opportunity_data)
        opportunity_id = create_response.json()["id"]
        
        score_data = {
            "opportunity_id": opportunity_id,
            "profile": {
                "user_id": sample_user_id,
                "display_name": "Test User",
                "skills": ["Communication", "Organization"],
                "tags": ["experienced"],
                "availability": []
            }
        }
        
        response = client.post("/api/v1/volunteer-matching/calculate-score", json=score_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_score" in data
        assert "skill_match_score" in data
        assert "availability_score" in data
        assert "preference_score" in data
        assert "distance_score" in data
        
        # Scores should be between 0.0 and 1.0
        for score_key in ["total_score", "skill_match_score", "availability_score", "preference_score", "distance_score"]:
            assert 0.0 <= data[score_key] <= 1.0
    
    def test_expire_old_requests(self, client):
        """Test POST /api/v1/volunteer-matching/expire-requests"""
        expire_data = {"days_old": 30}
        
        response = client.post("/api/v1/volunteer-matching/expire-requests", json=expire_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "expired_count" in data
        assert isinstance(data["expired_count"], int)
        assert data["expired_count"] >= 0