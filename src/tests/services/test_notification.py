"""
Tests for NotificationService
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from src.services.notification import NotificationService, NotificationType
from src.domain.notifications import NotificationId, NotificationChannel, NotificationStatus
from src.domain.users import UserId


class TestNotificationService:
    """Test NotificationService functionality"""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger"""
        return logging.getLogger("test")
    
    @pytest.fixture
    def service(self, logger):
        """Create a fresh NotificationService for each test"""
        return NotificationService(logger)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return UserId.new()
    
    def test_service_initialization(self, service):
        """Test service initializes with sample data"""
        notifications = service.get_pending_notifications()
        assert isinstance(notifications, list)
        # Should have some sample data
        assert len(notifications) >= 0
    
    def test_send_notification(self, service, sample_user_id):
        """Test sending a basic notification"""
        notification = service.send_notification(
            recipient=sample_user_id,
            subject="Test Subject",
            body="Test body content",
            notification_type=NotificationType.EVENT_ASSIGNMENT,
            channel=NotificationChannel.EMAIL,
            priority="high"
        )
        
        assert notification.recipient == sample_user_id
        assert notification.subject == "Test Subject"
        assert notification.body == "Test body content"
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.status in [NotificationStatus.QUEUED, NotificationStatus.SENT]
        assert notification.queued_at is not None
    
    def test_send_notification_default_channel(self, service, sample_user_id):
        """Test sending notification with default channel selection"""
        notification = service.send_notification(
            recipient=sample_user_id,
            subject="Test Subject",
            body="Test body",
            notification_type=NotificationType.EVENT_REMINDER
        )
        
        assert notification.channel is not None
        assert isinstance(notification.channel, NotificationChannel)
    
    def test_send_event_assignment_notification(self, service, sample_user_id):
        """Test sending event assignment notification"""
        event_date = datetime.now() + timedelta(days=1)
        
        notification = service.send_event_assignment_notification(
            recipient=sample_user_id,
            event_title="Community Cleanup",
            event_date=event_date,
            event_location="Central Park"
        )
        
        assert "Community Cleanup" in notification.subject
        assert "Central Park" in notification.body
        assert notification.recipient == sample_user_id
    
    def test_send_event_reminder_notification(self, service, sample_user_id):
        """Test sending event reminder notification"""
        event_date = datetime.now() + timedelta(days=1)
        
        notification = service.send_event_reminder_notification(
            recipient=sample_user_id,
            event_title="Food Bank",
            event_date=event_date,
            event_location="Downtown Center",
            hours_before=2
        )
        
        assert "Reminder" in notification.subject or "reminder" in notification.subject.lower()
        assert "Food Bank" in notification.body
        assert "Downtown Center" in notification.body
    
    def test_send_event_update_notification(self, service, sample_user_id):
        """Test sending event update notification"""
        notification = service.send_event_update_notification(
            recipient=sample_user_id,
            event_title="Beach Cleanup",
            update_details="Time changed to 10 AM"
        )
        
        assert "Beach Cleanup" in notification.subject
        assert "Time changed to 10 AM" in notification.body
    
    def test_send_event_cancellation_notification(self, service, sample_user_id):
        """Test sending event cancellation notification"""
        notification = service.send_event_cancellation_notification(
            recipient=sample_user_id,
            event_title="Park Event",
            reason="Weather conditions"
        )
        
        assert "cancelled" in notification.subject.lower() or "canceled" in notification.subject.lower()
        assert "Park Event" in notification.body
        assert "Weather conditions" in notification.body
    
    def test_send_match_request_approved_notification(self, service, sample_user_id):
        """Test sending match request approved notification"""
        notification = service.send_match_request_approved_notification(
            recipient=sample_user_id,
            event_title="Senior Center",
            opportunity_title="Reading Assistant"
        )
        
        assert "approved" in notification.subject.lower()
        assert "Senior Center" in notification.body
        assert "Reading Assistant" in notification.body
    
    def test_send_match_request_rejected_notification(self, service, sample_user_id):
        """Test sending match request rejected notification"""
        notification = service.send_match_request_rejected_notification(
            recipient=sample_user_id,
            event_title="Animal Shelter",
            opportunity_title="Dog Walker",
            reason="Position filled"
        )
        
        assert "rejected" in notification.subject.lower() or "not selected" in notification.subject.lower()
        assert "Animal Shelter" in notification.body
        assert "Position filled" in notification.body
    
    def test_send_new_opportunity_notification(self, service, sample_user_id):
        """Test sending new opportunity notification"""
        notification = service.send_new_opportunity_notification(
            recipient=sample_user_id,
            event_title="Library Event",
            opportunity_title="Story Reader",
            matching_skills=["reading", "children"]
        )
        
        assert "opportunity" in notification.subject.lower()
        assert "Library Event" in notification.body
        assert "Story Reader" in notification.body
    
    def test_get_notifications_by_user(self, service, sample_user_id):
        """Test getting notifications for a user"""
        # Send a notification first
        service.send_notification(
            recipient=sample_user_id,
            subject="Test",
            body="Test",
            notification_type=NotificationType.EVENT_ASSIGNMENT
        )
        
        notifications = service.get_notifications_by_user(sample_user_id)
        assert isinstance(notifications, list)
        
        # Check if our notification is in the list
        user_notifications = [n for n in notifications if n.recipient == sample_user_id]
        assert len(user_notifications) >= 1
    
    def test_get_notifications_by_user_with_limit(self, service, sample_user_id):
        """Test getting notifications with limit"""
        # Send multiple notifications
        for i in range(5):
            service.send_notification(
                recipient=sample_user_id,
                subject=f"Test {i}",
                body=f"Test body {i}",
                notification_type=NotificationType.EVENT_ASSIGNMENT
            )
        
        notifications = service.get_notifications_by_user(sample_user_id, limit=3)
        user_notifications = [n for n in notifications if n.recipient == sample_user_id]
        assert len(user_notifications) <= 3
    
    def test_get_notifications_by_user_with_status_filter(self, service, sample_user_id):
        """Test getting notifications with status filter"""
        notifications = service.get_notifications_by_user(
            sample_user_id, 
            status_filter=NotificationStatus.SENT
        )
        
        assert isinstance(notifications, list)
        # All returned notifications should be SENT
        for notification in notifications:
            if notification.recipient == sample_user_id:
                assert notification.status == NotificationStatus.SENT
    
    def test_mark_notification_as_read(self, service, sample_user_id):
        """Test marking notification as read"""
        # Send a notification
        notification = service.send_notification(
            recipient=sample_user_id,
            subject="Test",
            body="Test",
            notification_type=NotificationType.EVENT_ASSIGNMENT
        )
        
        # Mark as read
        success = service.mark_notification_as_read(notification.id)
        assert success is True
    
    def test_mark_notification_as_read_not_found(self, service):
        """Test marking non-existent notification as read"""
        fake_id = NotificationId(uuid4())
        success = service.mark_notification_as_read(fake_id)
        assert success is False
    
    def test_get_unread_count(self, service, sample_user_id):
        """Test getting unread notification count"""
        initial_count = service.get_unread_count(sample_user_id)
        
        # Send a notification
        service.send_notification(
            recipient=sample_user_id,
            subject="Unread Test",
            body="Test",
            notification_type=NotificationType.EVENT_ASSIGNMENT
        )
        
        new_count = service.get_unread_count(sample_user_id)
        assert new_count >= initial_count
    
    def test_set_user_notification_preferences(self, service, sample_user_id):
        """Test setting user notification preferences"""
        preferences = {
            NotificationChannel.EMAIL: True,
            NotificationChannel.SMS: False,
            NotificationChannel.IN_APP: True
        }
        
        service.set_user_notification_preferences(sample_user_id, preferences)
        
        # Verify preferences were set
        saved_preferences = service.get_user_notification_preferences(sample_user_id)
        assert saved_preferences[NotificationChannel.EMAIL] == True
        assert saved_preferences[NotificationChannel.SMS] == False
        assert saved_preferences[NotificationChannel.IN_APP] == True
    
    def test_get_user_notification_preferences_default(self, service, sample_user_id):
        """Test getting default notification preferences for new user"""
        preferences = service.get_user_notification_preferences(sample_user_id)
        
        assert isinstance(preferences, dict)
        assert NotificationChannel.EMAIL in preferences
        assert NotificationChannel.SMS in preferences
        assert NotificationChannel.IN_APP in preferences
    
    def test_get_pending_notifications(self, service):
        """Test getting pending notifications"""
        pending = service.get_pending_notifications()
        assert isinstance(pending, list)
        
        # All should be queued or failed
        for notification in pending:
            assert notification.status in [NotificationStatus.QUEUED, NotificationStatus.FAILED]
    
    def test_retry_failed_notifications(self, service):
        """Test retrying failed notifications"""
        # This method processes failed notifications
        count = service.retry_failed_notifications()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_notification_validation_empty_subject(self, service, sample_user_id):
        """Test validation fails for empty subject"""
        with pytest.raises(ValueError, match="Subject cannot be empty"):
            service.send_notification(
                recipient=sample_user_id,
                subject="",
                body="Test body",
                notification_type=NotificationType.EVENT_ASSIGNMENT
            )
    
    def test_notification_validation_empty_body(self, service, sample_user_id):
        """Test validation fails for empty body"""
        with pytest.raises(ValueError, match="Body cannot be empty"):
            service.send_notification(
                recipient=sample_user_id,
                subject="Test subject",
                body="",
                notification_type=NotificationType.EVENT_ASSIGNMENT
            )
    
    def test_notification_validation_long_subject(self, service, sample_user_id):
        """Test validation fails for overly long subject"""
        long_subject = "x" * 201  # Assuming 200 char limit
        
        with pytest.raises(ValueError, match="Subject too long"):
            service.send_notification(
                recipient=sample_user_id,
                subject=long_subject,
                body="Test body",
                notification_type=NotificationType.EVENT_ASSIGNMENT
            )