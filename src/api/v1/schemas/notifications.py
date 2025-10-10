from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
from enum import Enum


class NotificationChannelEnum(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"  
    PUSH = "PUSH"
    IN_APP = "IN_APP"


class NotificationStatusEnum(str, Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationTypeEnum(str, Enum):
    EVENT_ASSIGNMENT = "event_assignment"
    EVENT_UPDATE = "event_update"
    EVENT_REMINDER = "event_reminder"
    EVENT_CANCELLATION = "event_cancellation"
    MATCH_REQUEST_APPROVED = "match_request_approved"
    MATCH_REQUEST_REJECTED = "match_request_rejected"
    NEW_OPPORTUNITY = "new_opportunity"
    PROFILE_UPDATE_REMINDER = "profile_update_reminder"


class SendNotificationSchema(BaseModel):
    recipient_id: UUID = Field(..., description="Recipient user ID")
    subject: str = Field(..., min_length=1, max_length=200, description="Notification subject")
    body: str = Field(..., min_length=1, max_length=2000, description="Notification body")
    notification_type: NotificationTypeEnum = Field(..., description="Type of notification")
    channel: Optional[NotificationChannelEnum] = Field(None, description="Preferred channel")
    priority: str = Field("normal", description="Priority level")
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ["low", "normal", "high", "urgent"]:
            raise ValueError('Priority must be one of: low, normal, high, urgent')
        return v


class EventAssignmentNotificationSchema(BaseModel):
    recipient_id: UUID = Field(..., description="Recipient user ID")
    event_title: str = Field(..., description="Event title")
    event_date: datetime = Field(..., description="Event date")
    event_location: str = Field(..., description="Event location")


class EventReminderNotificationSchema(BaseModel):
    recipient_id: UUID = Field(..., description="Recipient user ID")
    event_title: str = Field(..., description="Event title")
    event_date: datetime = Field(..., description="Event date")
    event_location: str = Field(..., description="Event location")
    hours_before: int = Field(24, gt=0, description="Hours before event")


class EventUpdateNotificationSchema(BaseModel):
    recipient_id: UUID = Field(..., description="Recipient user ID")
    event_title: str = Field(..., description="Event title")
    update_details: str = Field(..., description="Update details")


class EventCancellationNotificationSchema(BaseModel):
    recipient_id: UUID = Field(..., description="Recipient user ID")
    event_title: str = Field(..., description="Event title")
    reason: Optional[str] = Field(None, description="Cancellation reason")


class MatchRequestNotificationSchema(BaseModel):
    recipient_id: UUID = Field(..., description="Recipient user ID")
    event_title: str = Field(..., description="Event title")
    opportunity_title: str = Field(..., description="Opportunity title")
    reason: Optional[str] = Field(None, description="Reason for rejection (if applicable)")


class NewOpportunityNotificationSchema(BaseModel):
    recipient_id: UUID = Field(..., description="Recipient user ID")
    event_title: str = Field(..., description="Event title")
    opportunity_title: str = Field(..., description="Opportunity title")
    matching_skills: List[str] = Field(..., description="Matching skills")


class NotificationResponseSchema(BaseModel):
    id: UUID
    recipient: UUID
    subject: str
    body: str
    channel: NotificationChannelEnum
    status: NotificationStatusEnum
    queued_at: Optional[datetime]
    sent_at: Optional[datetime]
    error: Optional[str]
    
    class Config:
        from_attributes = True


class NotificationListResponseSchema(BaseModel):
    notifications: List[NotificationResponseSchema]
    total: int
    unread_count: int


class NotificationPreferencesSchema(BaseModel):
    email: bool = Field(True, description="Enable email notifications")
    sms: bool = Field(False, description="Enable SMS notifications")
    push: bool = Field(True, description="Enable push notifications")
    in_app: bool = Field(True, description="Enable in-app notifications")


class NotificationPreferencesResponseSchema(BaseModel):
    user_id: UUID
    preferences: Dict[NotificationChannelEnum, bool]