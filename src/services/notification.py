from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from src.domain.notifications import (
    Notification, NotificationId, NotificationChannel, NotificationStatus
)
from src.domain.users import UserId
from config.logging_config import logger


class NotificationType(Enum):
    """Types of notifications that can be sent."""
    EVENT_ASSIGNMENT = "event_assignment"
    EVENT_UPDATE = "event_update"
    EVENT_REMINDER = "event_reminder"
    EVENT_CANCELLATION = "event_cancellation"
    MATCH_REQUEST_APPROVED = "match_request_approved"
    MATCH_REQUEST_REJECTED = "match_request_rejected"
    NEW_OPPORTUNITY = "new_opportunity"
    PROFILE_UPDATE_REMINDER = "profile_update_reminder"


class NotificationService:
    """Service for sending notifications to volunteers for event assignments, updates, and reminders."""
    
    def __init__(self):
        # Hard-coded data storage (no database implementation)
        self._notifications: dict[str, Notification] = {}
        self._user_preferences: dict[str, Dict[NotificationChannel, bool]] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self) -> None:
        """Initialize with sample notifications and user preferences."""
        # Sample notification 1
        user1_id = UserId.new()
        notif1_id = NotificationId.new()
        notification1 = Notification(
            id=notif1_id,
            recipient=user1_id,
            subject="Event Assignment Confirmation",
            body="You have been assigned to the Community Park Cleanup event on March 15th. Please confirm your attendance.",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            queued_at=datetime.now() - timedelta(hours=2),
            sent_at=datetime.now() - timedelta(hours=1)
        )
        self._notifications[str(notif1_id.value)] = notification1
        
        # Sample notification 2
        user2_id = UserId.new()
        notif2_id = NotificationId.new()
        notification2 = Notification(
            id=notif2_id,
            recipient=user2_id,
            subject="Event Reminder",
            body="Reminder: Food Bank Distribution event tomorrow at 9:00 AM. Location: Houston Food Bank",
            channel=NotificationChannel.SMS,
            status=NotificationStatus.QUEUED,
            queued_at=datetime.now() - timedelta(minutes=30)
        )
        self._notifications[str(notif2_id.value)] = notification2
        
        # Sample notification 3
        user3_id = UserId.new()
        notif3_id = NotificationId.new()
        notification3 = Notification(
            id=notif3_id,
            recipient=user3_id,
            subject="Match Request Approved",
            body="Great news! Your application for the Senior Center Activities event has been approved.",
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.SENT,
            queued_at=datetime.now() - timedelta(days=1),
            sent_at=datetime.now() - timedelta(hours=23)
        )
        self._notifications[str(notif3_id.value)] = notification3
        
        # Sample user preferences
        self._user_preferences[str(user1_id.value)] = {
            NotificationChannel.EMAIL: True,
            NotificationChannel.SMS: False,
            NotificationChannel.PUSH: True,
            NotificationChannel.IN_APP: True
        }
        
        self._user_preferences[str(user2_id.value)] = {
            NotificationChannel.EMAIL: True,
            NotificationChannel.SMS: True,
            NotificationChannel.PUSH: False,
            NotificationChannel.IN_APP: True
        }
        
        logger.info(f"Initialized {len(self._notifications)} sample notifications")
    
    def send_notification(
        self,
        recipient: UserId,
        subject: str,
        body: str,
        notification_type: NotificationType,
        channel: Optional[NotificationChannel] = None,
        priority: str = "normal"
    ) -> Notification:
        """Send a notification to a user."""
        # Validation
        if not subject or len(subject.strip()) == 0:
            raise ValueError("Subject is required")
        if len(subject) > 200:
            raise ValueError("Subject must be 200 characters or less")
        
        if not body or len(body.strip()) == 0:
            raise ValueError("Body is required")
        if len(body) > 2000:
            raise ValueError("Body must be 2000 characters or less")
        
        if priority not in ["low", "normal", "high", "urgent"]:
            raise ValueError("Priority must be one of: low, normal, high, urgent")
        
        # Determine channel if not specified
        if channel is None:
            channel = self._get_preferred_channel(recipient, notification_type)
        
        # Check if user has enabled this channel
        if not self._is_channel_enabled(recipient, channel):
            logger.warning(f"Channel {channel.name} is disabled for user {recipient.value}")
            # Fall back to IN_APP if available
            if self._is_channel_enabled(recipient, NotificationChannel.IN_APP):
                channel = NotificationChannel.IN_APP
            else:
                raise ValueError("No enabled notification channels for user")
        
        # Create notification
        notification_id = NotificationId.new()
        notification = Notification(
            id=notification_id,
            recipient=recipient,
            subject=subject.strip(),
            body=body.strip(),
            channel=channel,
            status=NotificationStatus.QUEUED,
            queued_at=datetime.now()
        )
        
        self._notifications[str(notification_id.value)] = notification
        
        # Simulate sending (in real implementation, this would integrate with email/SMS services)
        self._process_notification(notification)
        
        logger.info(f"Sent {notification_type.value} notification to user {recipient.value}")
        return notification
    
    def send_event_assignment_notification(
        self,
        recipient: UserId,
        event_title: str,
        event_date: datetime,
        event_location: str
    ) -> Notification:
        """Send notification for event assignment."""
        subject = f"Event Assignment: {event_title}"
        body = (
            f"You have been assigned to the '{event_title}' event.\n\n"
            f"Date: {event_date.strftime('%B %d, %Y at %I:%M %p')}\n"
            f"Location: {event_location}\n\n"
            f"Please confirm your attendance and prepare accordingly."
        )
        
        return self.send_notification(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.EVENT_ASSIGNMENT,
            priority="normal"
        )
    
    def send_event_reminder_notification(
        self,
        recipient: UserId,
        event_title: str,
        event_date: datetime,
        event_location: str,
        hours_before: int = 24
    ) -> Notification:
        """Send reminder notification before an event."""
        subject = f"Reminder: {event_title}"
        
        if hours_before >= 24:
            time_desc = f"{hours_before // 24} day(s)"
        else:
            time_desc = f"{hours_before} hour(s)"
        
        body = (
            f"Reminder: You have a volunteer event in {time_desc}.\n\n"
            f"Event: {event_title}\n"
            f"Date: {event_date.strftime('%B %d, %Y at %I:%M %p')}\n"
            f"Location: {event_location}\n\n"
            f"Please arrive on time and bring any necessary items."
        )
        
        return self.send_notification(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.EVENT_REMINDER,
            priority="normal"
        )
    
    def send_event_update_notification(
        self,
        recipient: UserId,
        event_title: str,
        update_details: str
    ) -> Notification:
        """Send notification for event updates."""
        subject = f"Event Update: {event_title}"
        body = (
            f"There has been an update to the '{event_title}' event:\n\n"
            f"{update_details}\n\n"
            f"Please review the changes and adjust your plans accordingly."
        )
        
        return self.send_notification(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.EVENT_UPDATE,
            priority="high"
        )
    
    def send_event_cancellation_notification(
        self,
        recipient: UserId,
        event_title: str,
        reason: Optional[str] = None
    ) -> Notification:
        """Send notification for event cancellation."""
        subject = f"Event Cancelled: {event_title}"
        body = f"Unfortunately, the '{event_title}' event has been cancelled."
        
        if reason:
            body += f"\n\nReason: {reason}"
        
        body += "\n\nWe apologize for any inconvenience. Please check for other available volunteer opportunities."
        
        return self.send_notification(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.EVENT_CANCELLATION,
            priority="high"
        )
    
    def send_match_request_approved_notification(
        self,
        recipient: UserId,
        event_title: str,
        opportunity_title: str
    ) -> Notification:
        """Send notification when a match request is approved."""
        subject = "Volunteer Application Approved"
        body = (
            f"Great news! Your application has been approved.\n\n"
            f"Event: {event_title}\n"
            f"Role: {opportunity_title}\n\n"
            f"You will receive further details about the event soon."
        )
        
        return self.send_notification(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.MATCH_REQUEST_APPROVED,
            priority="normal"
        )
    
    def send_match_request_rejected_notification(
        self,
        recipient: UserId,
        event_title: str,
        opportunity_title: str,
        reason: Optional[str] = None
    ) -> Notification:
        """Send notification when a match request is rejected."""
        subject = "Volunteer Application Update"
        body = (
            f"Thank you for your interest in volunteering.\n\n"
            f"Event: {event_title}\n"
            f"Role: {opportunity_title}\n\n"
            f"Unfortunately, we are unable to accept your application at this time."
        )
        
        if reason:
            body += f"\n\nReason: {reason}"
        
        body += "\n\nPlease check for other available volunteer opportunities."
        
        return self.send_notification(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.MATCH_REQUEST_REJECTED,
            priority="normal"
        )
    
    def send_new_opportunity_notification(
        self,
        recipient: UserId,
        event_title: str,
        opportunity_title: str,
        matching_skills: List[str]
    ) -> Notification:
        """Send notification about new opportunities matching user's skills."""
        subject = "New Volunteer Opportunity"
        body = (
            f"A new volunteer opportunity matches your skills!\n\n"
            f"Event: {event_title}\n"
            f"Role: {opportunity_title}\n"
            f"Matching Skills: {', '.join(matching_skills)}\n\n"
            f"Apply now to secure your spot!"
        )
        
        return self.send_notification(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.NEW_OPPORTUNITY,
            priority="normal"
        )
    
    def get_notifications_by_user(
        self,
        user_id: UserId,
        limit: Optional[int] = None,
        status_filter: Optional[NotificationStatus] = None
    ) -> List[Notification]:
        """Get notifications for a specific user."""
        user_notifications = [
            notif for notif in self._notifications.values()
            if notif.recipient.value == user_id.value
        ]
        
        if status_filter:
            user_notifications = [
                notif for notif in user_notifications
                if notif.status == status_filter
            ]
        
        # Sort by queued_at (most recent first)
        user_notifications.sort(key=lambda x: x.queued_at or datetime.min, reverse=True)
        
        if limit:
            user_notifications = user_notifications[:limit]
        
        return user_notifications
    
    def mark_notification_as_read(self, notification_id: NotificationId) -> bool:
        """Mark a notification as read (for in-app notifications)."""
        notification = self._notifications.get(str(notification_id.value))
        if not notification:
            return False
        
        # For demo purposes, we'll just log this
        # In real implementation, you'd update a "read" status
        logger.info(f"Marked notification {notification_id.value} as read")
        return True
    
    def get_unread_count(self, user_id: UserId) -> int:
        """Get count of unread in-app notifications for a user."""
        # For demo purposes, return a count of in-app notifications
        # In real implementation, you'd track read status
        in_app_notifications = [
            notif for notif in self._notifications.values()
            if (notif.recipient.value == user_id.value and
                notif.channel == NotificationChannel.IN_APP and
                notif.status == NotificationStatus.SENT)
        ]
        return len(in_app_notifications)
    
    def set_user_notification_preferences(
        self,
        user_id: UserId,
        preferences: Dict[NotificationChannel, bool]
    ) -> None:
        """Set notification channel preferences for a user."""
        # Validation
        valid_channels = set(NotificationChannel)
        provided_channels = set(preferences.keys())
        
        if not provided_channels.issubset(valid_channels):
            invalid_channels = provided_channels - valid_channels
            raise ValueError(f"Invalid notification channels: {invalid_channels}")
        
        self._user_preferences[str(user_id.value)] = preferences.copy()
        logger.info(f"Updated notification preferences for user {user_id.value}")
    
    def get_user_notification_preferences(self, user_id: UserId) -> Dict[NotificationChannel, bool]:
        """Get notification channel preferences for a user."""
        return self._user_preferences.get(str(user_id.value), {
            NotificationChannel.EMAIL: True,
            NotificationChannel.SMS: False,
            NotificationChannel.PUSH: True,
            NotificationChannel.IN_APP: True
        })
    
    def get_pending_notifications(self) -> List[Notification]:
        """Get all notifications that are queued but not yet sent."""
        return [
            notif for notif in self._notifications.values()
            if notif.status == NotificationStatus.QUEUED
        ]
    
    def retry_failed_notifications(self) -> int:
        """Retry sending failed notifications."""
        failed_notifications = [
            notif for notif in self._notifications.values()
            if notif.status == NotificationStatus.FAILED
        ]
        
        retry_count = 0
        for notification in failed_notifications:
            notification.status = NotificationStatus.QUEUED
            notification.error = None
            self._process_notification(notification)
            retry_count += 1
        
        logger.info(f"Retried {retry_count} failed notifications")
        return retry_count
    
    def _get_preferred_channel(self, user_id: UserId, notification_type: NotificationType) -> NotificationChannel:
        """Get the preferred notification channel for a user and notification type."""
        preferences = self.get_user_notification_preferences(user_id)
        
        # Priority order based on notification type
        if notification_type in [NotificationType.EVENT_CANCELLATION, NotificationType.EVENT_UPDATE]:
            # High priority notifications - prefer immediate channels
            if preferences.get(NotificationChannel.SMS, False):
                return NotificationChannel.SMS
            elif preferences.get(NotificationChannel.PUSH, False):
                return NotificationChannel.PUSH
        
        # Default preference order
        if preferences.get(NotificationChannel.EMAIL, False):
            return NotificationChannel.EMAIL
        elif preferences.get(NotificationChannel.IN_APP, False):
            return NotificationChannel.IN_APP
        elif preferences.get(NotificationChannel.PUSH, False):
            return NotificationChannel.PUSH
        elif preferences.get(NotificationChannel.SMS, False):
            return NotificationChannel.SMS
        
        # Fallback
        return NotificationChannel.IN_APP
    
    def _is_channel_enabled(self, user_id: UserId, channel: NotificationChannel) -> bool:
        """Check if a notification channel is enabled for a user."""
        preferences = self.get_user_notification_preferences(user_id)
        return preferences.get(channel, False)
    
    def _process_notification(self, notification: Notification) -> None:
        """Process/send a notification (simulated for demo)."""
        try:
            # Simulate processing time and potential failures
            import random
            
            if random.random() < 0.1:  # 10% chance of failure for demo
                notification.status = NotificationStatus.FAILED
                notification.error = "Simulated delivery failure"
            else:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now()
            
            logger.info(f"Processed notification {notification.id.value} via {notification.channel.name}")
            
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.error = str(e)
            logger.error(f"Failed to process notification {notification.id.value}: {e}")
