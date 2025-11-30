from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID

from src.services.notification import NotificationService, NotificationType
from src.domain.users import UserId
from src.domain.notifications import NotificationId, NotificationChannel
from src.repositories.database import get_uow, get_uow_manager
from src.repositories.unit_of_work import UnitOfWorkManager
from ..schemas.notifications import (
    SendNotificationSchema, EventAssignmentNotificationSchema,
    EventReminderNotificationSchema, EventUpdateNotificationSchema,
    EventCancellationNotificationSchema, MatchRequestNotificationSchema,
    NewOpportunityNotificationSchema, NotificationResponseSchema,
    NotificationListResponseSchema, NotificationPreferencesSchema,
    NotificationPreferencesResponseSchema, NotificationChannelEnum,
    NotificationTypeEnum
)
from src.config.logging_config import logger

router = APIRouter(prefix="/notifications", tags=["notifications"])

#region helpers

def _get_notification_service() -> NotificationService:
    return NotificationService(get_uow_manager(), logger)

# helper to convert from dataclass model -> pydantic schema
def _convert_notification_to_response(notification) -> NotificationResponseSchema:
    """Convert domain Notification to NotificationResponseSchema."""
    return NotificationResponseSchema(
        id=notification.id.value,
        recipient=notification.recipient.value,
        subject=notification.subject,
        body=notification.body,
        channel=NotificationChannelEnum(notification.channel.name),
        status=notification.status.name,
        queued_at=notification.queued_at,
        sent_at=notification.sent_at,
        error=notification.error
    )


def _convert_enum_to_domain_channel(channel_enum: NotificationChannelEnum) -> NotificationChannel:
    """Convert NotificationChannelEnum to domain NotificationChannel."""
    return NotificationChannel[channel_enum.value]


def _convert_enum_to_domain_type(type_enum: NotificationTypeEnum) -> NotificationType:
    """Convert NotificationTypeEnum to domain NotificationType."""
    return NotificationType(type_enum.value)

#endregion

@router.get("/user/{user_id}", response_model=NotificationListResponseSchema)
async def get_user_notifications(
    user_id: UUID,
    limit: Optional[int] = None,
    status_filter: Optional[str] = None,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Get notifications for a specific user."""
    try:
        from src.domain.notifications import NotificationStatus
        
        # Convert status filter if provided
        status_enum = None
        if status_filter:
            try:
                status_enum = NotificationStatus[status_filter.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        notifications = notification_service.get_notifications_by_user(
            user_id=UserId(user_id),
            limit=limit,
            status_filter=status_enum
        )
        
        unread_count = notification_service.get_unread_count(UserId(user_id))
        
        notification_responses = [
            _convert_notification_to_response(notif) for notif in notifications
        ]
        
        return NotificationListResponseSchema(
            notifications=notification_responses,
            total=len(notification_responses),
            unread_count=unread_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notifications for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.post("/send", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def send_notification(
    notification_data: SendNotificationSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Send a custom notification."""
    try:
        # Convert enums to domain types
        notification_type = _convert_enum_to_domain_type(notification_data.notification_type)
        channel = None
        if notification_data.channel:
            channel = _convert_enum_to_domain_channel(notification_data.channel)
        
        notification = notification_service.send_notification(
            recipient=UserId(notification_data.recipient_id),
            subject=notification_data.subject,
            body=notification_data.body,
            notification_type=notification_type,
            channel=channel,
            priority=notification_data.priority
        )
        
        return _convert_notification_to_response(notification)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification"
        )


@router.post("/event-assignment", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def send_event_assignment_notification(
    notification_data: EventAssignmentNotificationSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Send an event assignment notification."""
    try:
        notification = notification_service.send_event_assignment_notification(
            recipient=UserId(notification_data.recipient_id),
            event_title=notification_data.event_title,
            event_date=notification_data.event_date,
            event_location=notification_data.event_location
        )
        
        return _convert_notification_to_response(notification)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error sending event assignment notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send event assignment notification"
        )


@router.post("/event-reminder", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def send_event_reminder_notification(
    notification_data: EventReminderNotificationSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Send an event reminder notification."""
    try:
        notification = notification_service.send_event_reminder_notification(
            recipient=UserId(notification_data.recipient_id),
            event_title=notification_data.event_title,
            event_date=notification_data.event_date,
            event_location=notification_data.event_location,
            hours_before=notification_data.hours_before
        )
        
        return _convert_notification_to_response(notification)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error sending event reminder notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send event reminder notification"
        )


@router.post("/event-update", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def send_event_update_notification(
    notification_data: EventUpdateNotificationSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Send an event update notification."""
    try:
        notification = notification_service.send_event_update_notification(
            recipient=UserId(notification_data.recipient_id),
            event_title=notification_data.event_title,
            update_details=notification_data.update_details
        )
        
        return _convert_notification_to_response(notification)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error sending event update notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send event update notification"
        )


@router.post("/event-cancellation", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def send_event_cancellation_notification(
    notification_data: EventCancellationNotificationSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Send an event cancellation notification."""
    try:
        notification = notification_service.send_event_cancellation_notification(
            recipient=UserId(notification_data.recipient_id),
            event_title=notification_data.event_title,
            reason=notification_data.reason
        )
        
        return _convert_notification_to_response(notification)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error sending event cancellation notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send event cancellation notification"
        )


@router.post("/match-request-approved", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def send_match_request_approved_notification(
    notification_data: MatchRequestNotificationSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Send a match request approved notification."""
    try:
        notification = notification_service.send_match_request_approved_notification(
            recipient=UserId(notification_data.recipient_id),
            event_title=notification_data.event_title,
            opportunity_title=notification_data.opportunity_title
        )
        
        return _convert_notification_to_response(notification)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error sending match request approved notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send match request approved notification"
        )


@router.post("/match-request-rejected", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def send_match_request_rejected_notification(
    notification_data: MatchRequestNotificationSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Send a match request rejected notification."""
    try:
        notification = notification_service.send_match_request_rejected_notification(
            recipient=UserId(notification_data.recipient_id),
            event_title=notification_data.event_title,
            opportunity_title=notification_data.opportunity_title,
            reason=notification_data.reason
        )
        
        return _convert_notification_to_response(notification)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error sending match request rejected notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send match request rejected notification"
        )


@router.post("/new-opportunity", response_model=NotificationResponseSchema, status_code=status.HTTP_201_CREATED)
async def send_new_opportunity_notification(
    notification_data: NewOpportunityNotificationSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Send a new opportunity notification."""
    try:
        notification = notification_service.send_new_opportunity_notification(
            recipient=UserId(notification_data.recipient_id),
            event_title=notification_data.event_title,
            opportunity_title=notification_data.opportunity_title,
            matching_skills=notification_data.matching_skills
        )
        
        return _convert_notification_to_response(notification)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error sending new opportunity notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send new opportunity notification"
        )


@router.post("/{notification_id}/mark-read")
async def mark_notification_as_read(
    notification_id: UUID,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Mark a notification as read."""
    try:
        success = notification_service.mark_notification_as_read(NotificationId(notification_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification marked as read"}
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.get("/user/{user_id}/unread-count")
async def get_unread_count(
    user_id: UUID,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Get count of unread notifications for a user."""
    try:
        count = notification_service.get_unread_count(UserId(user_id))
        return {"user_id": user_id, "unread_count": count}
    except Exception as e:
        logger.error(f"Error getting unread count for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )


@router.get("/user/{user_id}/preferences", response_model=NotificationPreferencesResponseSchema)
async def get_user_notification_preferences(
    user_id: UUID,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Get notification preferences for a user."""
    try:
        preferences = notification_service.get_user_notification_preferences(UserId(user_id))
        
        # Convert domain preferences to enum preferences
        enum_preferences = {}
        for channel, enabled in preferences.items():
            enum_preferences[NotificationChannelEnum(channel.name)] = enabled
        
        return NotificationPreferencesResponseSchema(
            user_id=user_id,
            preferences=enum_preferences
        )
    except Exception as e:
        logger.error(f"Error getting notification preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification preferences"
        )


@router.put("/user/{user_id}/preferences")
async def set_user_notification_preferences(
    user_id: UUID,
    preferences_data: NotificationPreferencesSchema,
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Set notification preferences for a user."""
    try:
        # Convert schema to domain preferences
        domain_preferences = {
            NotificationChannel.EMAIL: preferences_data.email,
            NotificationChannel.SMS: preferences_data.sms,
            NotificationChannel.PUSH: preferences_data.push,
            NotificationChannel.IN_APP: preferences_data.in_app
        }
        
        notification_service.set_user_notification_preferences(
            user_id=UserId(user_id),
            preferences=domain_preferences
        )
        
        return {"message": "Notification preferences updated successfully"}
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error setting notification preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set notification preferences"
        )


@router.get("/pending", response_model=List[NotificationResponseSchema])
async def get_pending_notifications(
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Get all pending notifications."""
    try:
        notifications = notification_service.get_pending_notifications()
        return [_convert_notification_to_response(notif) for notif in notifications]
    except Exception as e:
        logger.error(f"Error getting pending notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending notifications"
        )


@router.post("/retry-failed")
async def retry_failed_notifications(
    notification_service: NotificationService = Depends(_get_notification_service)
):
    """Retry sending failed notifications."""
    try:
        retry_count = notification_service.retry_failed_notifications()
        return {"message": f"Retried {retry_count} failed notifications"}
    except Exception as e:
        logger.error(f"Error retrying failed notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry failed notifications"
        )
