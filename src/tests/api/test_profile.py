"""
Tests for Profile API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import time
from uuid import uuid4

from src.main import app


class TestProfileAPI:
    """Test Profile API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return str(uuid4())
    
    @pytest.fixture
    def sample_profile_data(self, sample_user_id):
        """Sample profile data for testing"""
        return {
            "user_id": sample_user_id,
            "display_name": "John Doe",
            "phone": "555-123-4567",
            "skills": ["Python", "Communication", "Leadership"],
            "tags": ["experienced", "reliable", "bilingual"],
            "availability": [
                {
                    "weekday": 1,
                    "start": "09:00:00",
                    "end": "17:00:00"
                },
                {
                    "weekday": 5,
                    "start": "10:00:00", 
                    "end": "16:00:00"
                }
            ]
        }
    
    def test_get_all_profiles(self, client):
        """Test GET /api/v1/profiles/"""
        response = client.get("/api/v1/profiles/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should return a list of profiles (may be empty or have sample data)
        for profile in data:
            assert "user_id" in profile
            assert "display_name" in profile
            assert "skills" in profile
            assert "tags" in profile
            assert "availability" in profile
    
    def test_create_profile(self, client, sample_profile_data):
        """Test POST /api/v1/profiles/"""
        response = client.post("/api/v1/profiles/", json=sample_profile_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["user_id"] == sample_profile_data["user_id"]
        assert data["display_name"] == sample_profile_data["display_name"]
        assert data["phone"] == sample_profile_data["phone"]
        assert data["skills"] == sample_profile_data["skills"]
        assert data["tags"] == sample_profile_data["tags"]
        assert len(data["availability"]) == len(sample_profile_data["availability"])
        assert "updated_at" in data
    
    def test_create_profile_minimal(self, client):
        """Test creating profile with minimal data"""
        minimal_data = {
            "user_id": str(uuid4()),
            "display_name": "Jane Smith"
        }
        
        response = client.post("/api/v1/profiles/", json=minimal_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["display_name"] == "Jane Smith"
        assert data["phone"] is None
        assert data["skills"] == []
        assert data["tags"] == []
        assert data["availability"] == []
    
    def test_create_profile_invalid_data(self, client):
        """Test POST /api/v1/profiles/ with invalid data"""
        invalid_data = {
            "user_id": str(uuid4()),
            "display_name": "",  # Empty display name
            "phone": "invalid-phone-format"
        }
        
        response = client.post("/api/v1/profiles/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_profile_by_user_id(self, client, sample_profile_data):
        """Test GET /api/v1/profiles/{user_id}"""
        # First create a profile
        create_response = client.post("/api/v1/profiles/", json=sample_profile_data)
        assert create_response.status_code == 201
        
        user_id = sample_profile_data["user_id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/profiles/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == user_id
        assert data["display_name"] == sample_profile_data["display_name"]
    
    def test_get_profile_by_user_id_not_found(self, client):
        """Test GET /api/v1/profiles/{user_id} with non-existent ID"""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/profiles/{fake_id}")
        assert response.status_code == 404
    
    def test_update_profile(self, client, sample_profile_data):
        """Test PUT /api/v1/profiles/{user_id}"""
        # First create a profile
        create_response = client.post("/api/v1/profiles/", json=sample_profile_data)
        assert create_response.status_code == 201
        
        user_id = sample_profile_data["user_id"]
        
        # Update data
        update_data = {
            "display_name": "Updated Name",
            "phone": "555-999-8888",
            "skills": ["Updated Skill"],
            "tags": ["updated_tag"]
        }
        
        # Update the profile
        response = client.put(f"/api/v1/profiles/{user_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["display_name"] == update_data["display_name"]
        assert data["phone"] == update_data["phone"]
        assert data["skills"] == update_data["skills"]
        assert data["tags"] == update_data["tags"]
    
    def test_update_profile_not_found(self, client):
        """Test PUT /api/v1/profiles/{user_id} with non-existent ID"""
        fake_id = str(uuid4())
        update_data = {"display_name": "Should Fail"}
        
        response = client.put(f"/api/v1/profiles/{fake_id}", json=update_data)
        assert response.status_code == 404
    
    def test_add_skill(self, client, sample_profile_data):
        """Test POST /api/v1/profiles/{user_id}/skills"""
        # Create profile
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        skill_data = {"skill": "New Skill"}
        
        response = client.post(f"/api/v1/profiles/{user_id}/skills", json=skill_data)
        assert response.status_code == 200
        
        # Verify skill was added
        profile_response = client.get(f"/api/v1/profiles/{user_id}")
        profile_data = profile_response.json()
        assert "New Skill" in profile_data["skills"]
    
    def test_add_skill_duplicate(self, client, sample_profile_data):
        """Test adding duplicate skill"""
        # Create profile with existing skill
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        # Try to add existing skill
        existing_skill = sample_profile_data["skills"][0]
        skill_data = {"skill": existing_skill}
        
        response = client.post(f"/api/v1/profiles/{user_id}/skills", json=skill_data)
        assert response.status_code == 422  # Should fail validation
    
    def test_remove_skill(self, client, sample_profile_data):
        """Test DELETE /api/v1/profiles/{user_id}/skills/{skill}"""
        # Create profile
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        skill_to_remove = sample_profile_data["skills"][0]
        
        response = client.delete(f"/api/v1/profiles/{user_id}/skills/{skill_to_remove}")
        assert response.status_code == 200
        
        # Verify skill was removed
        profile_response = client.get(f"/api/v1/profiles/{user_id}")
        profile_data = profile_response.json()
        assert skill_to_remove not in profile_data["skills"]
    
    def test_remove_skill_not_found(self, client, sample_profile_data):
        """Test removing skill that doesn't exist"""
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        response = client.delete(f"/api/v1/profiles/{user_id}/skills/NonExistentSkill")
        assert response.status_code == 404
    
    def test_add_tag(self, client, sample_profile_data):
        """Test POST /api/v1/profiles/{user_id}/tags"""
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        tag_data = {"tag": "new_tag"}
        
        response = client.post(f"/api/v1/profiles/{user_id}/tags", json=tag_data)
        assert response.status_code == 200
        
        # Verify tag was added
        profile_response = client.get(f"/api/v1/profiles/{user_id}")
        profile_data = profile_response.json()
        assert "new_tag" in profile_data["tags"]
    
    def test_remove_tag(self, client, sample_profile_data):
        """Test DELETE /api/v1/profiles/{user_id}/tags/{tag}"""
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        tag_to_remove = sample_profile_data["tags"][0]
        
        response = client.delete(f"/api/v1/profiles/{user_id}/tags/{tag_to_remove}")
        assert response.status_code == 200
        
        # Verify tag was removed
        profile_response = client.get(f"/api/v1/profiles/{user_id}")
        profile_data = profile_response.json()
        assert tag_to_remove not in profile_data["tags"]
    
    def test_add_availability_window(self, client, sample_profile_data):
        """Test POST /api/v1/profiles/{user_id}/availability"""
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        availability_data = {
            "weekday": 3,
            "start": "14:00:00",
            "end": "18:00:00"
        }
        
        response = client.post(f"/api/v1/profiles/{user_id}/availability", json=availability_data)
        assert response.status_code == 200
        
        # Verify availability was added
        profile_response = client.get(f"/api/v1/profiles/{user_id}")
        profile_data = profile_response.json()
        availability_found = any(
            av["weekday"] == 3 and av["start"] == "14:00:00"
            for av in profile_data["availability"]
        )
        assert availability_found
    
    def test_remove_availability_window(self, client, sample_profile_data):
        """Test DELETE /api/v1/profiles/{user_id}/availability"""
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        # Remove first availability window
        availability_to_remove = sample_profile_data["availability"][0]
        
        response = client.delete(f"/api/v1/profiles/{user_id}/availability", json=availability_to_remove)
        assert response.status_code == 200
        
        # Verify availability was removed
        profile_response = client.get(f"/api/v1/profiles/{user_id}")
        profile_data = profile_response.json()
        remaining_availability = [
            av for av in profile_data["availability"]
            if av["weekday"] == availability_to_remove["weekday"]
        ]
        assert len(remaining_availability) == 0
    
    def test_search_profiles_by_skills(self, client, sample_profile_data):
        """Test GET /api/v1/profiles/search/by-skills"""
        # Create profile
        client.post("/api/v1/profiles/", json=sample_profile_data)
        
        # Search by skills
        skill_to_search = sample_profile_data["skills"][0]
        response = client.get(f"/api/v1/profiles/search/by-skills?skills={skill_to_search}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Profile should be in results
        found_profile = any(
            profile["user_id"] == sample_profile_data["user_id"]
            for profile in data
        )
        assert found_profile
    
    def test_search_profiles_by_tags(self, client, sample_profile_data):
        """Test GET /api/v1/profiles/search/by-tags"""
        # Create profile
        client.post("/api/v1/profiles/", json=sample_profile_data)
        
        # Search by tags
        tag_to_search = sample_profile_data["tags"][0]
        response = client.get(f"/api/v1/profiles/search/by-tags?tags={tag_to_search}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Profile should be in results
        found_profile = any(
            profile["user_id"] == sample_profile_data["user_id"]
            for profile in data
        )
        assert found_profile
    
    def test_get_profile_stats(self, client, sample_profile_data):
        """Test GET /api/v1/profiles/{user_id}/stats"""
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        response = client.get(f"/api/v1/profiles/{user_id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_hours" in data
        assert "total_events" in data
        assert "recent_activity" in data
        assert isinstance(data["total_hours"], (int, float))
        assert isinstance(data["total_events"], int)
    
    def test_delete_profile(self, client, sample_profile_data):
        """Test DELETE /api/v1/profiles/{user_id}"""
        # Create profile
        client.post("/api/v1/profiles/", json=sample_profile_data)
        user_id = sample_profile_data["user_id"]
        
        # Delete profile
        response = client.delete(f"/api/v1/profiles/{user_id}")
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/profiles/{user_id}")
        assert get_response.status_code == 404
    
    def test_delete_profile_not_found(self, client):
        """Test deleting non-existent profile"""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/profiles/{fake_id}")
        assert response.status_code == 404