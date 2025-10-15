"""
Tests for Notifications API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from src.main import app


class TestNotificationsAPI:
    """Test Notifications API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return str(uuid4())
    
    @pytest.fixture
    def sample_notification_data(self, sample_user_id):
        """Sample notification data for testing"""
        return {
            "recipient_id": sample_user_id,
            "subject": "Test Notification",
            "body": "This is a test notification body",
            "notification_type": "event_assignment",
            "priority": "normal"
        }
    
    def test_send_notification(self, client, sample_notification_data):
        """Test POST /api/v1/notifications/send"""
        response = client.post("/api/v1/notifications/send", json=sample_notification_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["subject"] == sample_notification_data["subject"]
        assert data["body"] == sample_notification_data["body"]
    
    def test_get_user_notifications(self, client, sample_user_id):
        """Test GET /api/v1/notifications/user/{user_id}"""
        response = client.get(f"/api/v1/notifications/user/{sample_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        assert "unread_count" in data
        assert isinstance(data["notifications"], list)
    
    def test_get_unread_count(self, client, sample_user_id):
        """Test GET /api/v1/notifications/user/{user_id}/unread-count"""
        response = client.get(f"/api/v1/notifications/user/{sample_user_id}/unread-count")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
    
    def test_send_event_assignment_notification(self, client, sample_user_id):
        """Test POST /api/v1/notifications/event-assignment"""
        notification_data = {
            "recipient_id": sample_user_id,
            "event_title": "Test Event",
            "event_date": "2024-12-01T10:00:00",
            "event_location": "Test Location"
        }
        
        response = client.post("/api/v1/notifications/event-assignment", json=notification_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "subject" in data
        assert "body" in data
    
    def test_get_notification_preferences(self, client, sample_user_id):
        """Test GET /api/v1/notifications/user/{user_id}/preferences"""
        response = client.get(f"/api/v1/notifications/user/{sample_user_id}/preferences")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "preferences" in data
    
    def test_set_notification_preferences(self, client, sample_user_id):
        """Test PUT /api/v1/notifications/user/{user_id}/preferences"""
        preferences = {
            "email": True,
            "sms": False,
            "push": True,
            "in_app": True
        }
        
        response = client.put(
            f"/api/v1/notifications/user/{sample_user_id}/preferences",
            json=preferences
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_send_event_reminder_notification(self, client, sample_user_id):
        """Test POST /api/v1/notifications/event-reminder"""
        notification_data = {
            "recipient_id": sample_user_id,
            "event_title": "Community Cleanup",
            "event_date": "2024-12-01T10:00:00",
            "event_location": "Central Park",
            "hours_before": 24
        }
        
        response = client.post("/api/v1/notifications/event-reminder", json=notification_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "subject" in data
        assert "Community Cleanup" in data["subject"] or "Community Cleanup" in data["body"]
    
    def test_send_event_update_notification(self, client, sample_user_id):
        """Test POST /api/v1/notifications/event-update"""
        notification_data = {
            "recipient_id": sample_user_id,
            "event_title": "Food Bank Event",
            "update_details": "Location changed to downtown center"
        }
        
        response = client.post("/api/v1/notifications/event-update", json=notification_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "subject" in data
        assert "Food Bank Event" in data["body"]
    
    def test_send_event_cancellation_notification(self, client, sample_user_id):
        """Test POST /api/v1/notifications/event-cancellation"""
        notification_data = {
            "recipient_id": sample_user_id,
            "event_title": "Beach Cleanup",
            "reason": "Weather conditions"
        }
        
        response = client.post("/api/v1/notifications/event-cancellation", json=notification_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "subject" in data
        assert "cancelled" in data["subject"].lower() or "canceled" in data["subject"].lower()
    
    def test_send_match_request_approved_notification(self, client, sample_user_id):
        """Test POST /api/v1/notifications/match-request-approved"""
        notification_data = {
            "recipient_id": sample_user_id,
            "event_title": "Senior Center Activities",
            "opportunity_title": "Reading Assistant"
        }
        
        response = client.post("/api/v1/notifications/match-request-approved", json=notification_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "approved" in data["subject"].lower()
    
    def test_send_match_request_rejected_notification(self, client, sample_user_id):
        """Test POST /api/v1/notifications/match-request-rejected"""
        notification_data = {
            "recipient_id": sample_user_id,
            "event_title": "Animal Shelter",
            "opportunity_title": "Dog Walker",
            "reason": "Position filled"
        }
        
        response = client.post("/api/v1/notifications/match-request-rejected", json=notification_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "rejected" in data["subject"].lower() or "not selected" in data["subject"].lower()
    
    def test_send_new_opportunity_notification(self, client, sample_user_id):
        """Test POST /api/v1/notifications/new-opportunity"""
        notification_data = {
            "recipient_id": sample_user_id,
            "event_title": "Library Event",
            "opportunity_title": "Story Reader",
            "matching_skills": ["reading", "children"]
        }
        
        response = client.post("/api/v1/notifications/new-opportunity", json=notification_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert "opportunity" in data["subject"].lower()
    
    def test_mark_notification_as_read(self, client, sample_notification_data):
        """Test POST /api/v1/notifications/{notification_id}/mark-read"""
        # Send notification first
        send_response = client.post("/api/v1/notifications/send", json=sample_notification_data)
        notification_id = send_response.json()["id"]
        
        # Mark as read
        response = client.post(f"/api/v1/notifications/{notification_id}/mark-read")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_mark_notification_as_read_not_found(self, client):
        """Test marking non-existent notification as read"""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.post(f"/api/v1/notifications/{fake_id}/mark-read")
        assert response.status_code == 404
    
    def test_get_pending_notifications(self, client):
        """Test GET /api/v1/notifications/pending"""
        response = client.get("/api/v1/notifications/pending")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All notifications should be pending
        for notification in data:
            assert notification["status"] in ["QUEUED", "FAILED"]
    
    def test_retry_failed_notifications(self, client):
        """Test POST /api/v1/notifications/retry-failed"""
        response = client.post("/api/v1/notifications/retry-failed")
        assert response.status_code == 200
        
        data = response.json()
        assert "retried_count" in data
        assert isinstance(data["retried_count"], int)
    
    def test_get_user_notifications_with_filters(self, client, sample_user_id):
        """Test GET /api/v1/notifications/user/{user_id} with filters"""
        response = client.get(f"/api/v1/notifications/user/{sample_user_id}?limit=5&status_filter=SENT")
        assert response.status_code == 200
        
        data = response.json()
        assert "notifications" in data
        assert len(data["notifications"]) <= 5
        
        # All returned notifications should be SENT
        for notification in data["notifications"]:
            if notification["recipient"] == sample_user_id:
                assert notification["status"] == "SENT"
    
    def test_send_notification_invalid_data(self, client):
        """Test sending notification with invalid data"""
        invalid_data = {
            "recipient_id": "invalid-uuid",
            "subject": "",  # Empty subject
            "body": "",     # Empty body
            "notification_type": "invalid_type"
        }
        
        response = client.post("/api/v1/notifications/send", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_send_notification_missing_required_fields(self, client):
        """Test sending notification with missing required fields"""
        incomplete_data = {
            "subject": "Test Subject"
            # Missing recipient_id, body, notification_type
        }
        
        response = client.post("/api/v1/notifications/send", json=incomplete_data)
        assert response.status_code == 422  # Validation error
    
    def test_notification_preferences_validation(self, client, sample_user_id):
        """Test setting invalid notification preferences"""
        invalid_preferences = {
            "email": "not_a_boolean",
            "sms": "invalid",
            "invalid_channel": True
        }
        
        response = client.put(
            f"/api/v1/notifications/user/{sample_user_id}/preferences",
            json=invalid_preferences
        )
        assert response.status_code == 422  # Validation error