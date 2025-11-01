"""
SQLAlchemy database models for the volunteer management system.

These models map domain entities to database tables and handle
the persistence layer concerns like primary/foreign keys,
indexes, and table relationships.
"""
from __future__ import annotations
from datetime import datetime, time
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, DateTime, Integer, Float, Boolean, Text, Time,
    ForeignKey, Table, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ENUM
from src.config.database import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from src.config.database import schema_Name

# Enum definitions for database
class UserRoleEnum(Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    VOLUNTEER = "volunteer"

class EventStatusEnum(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"

class NotificationChannelEnum(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class NotificationStatusEnum(Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"

class MatchStatusEnum(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

# Association table for user roles (many-to-many)
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', PostgresUUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role', ENUM(UserRoleEnum), primary_key=True)
)

class UserModel(Base):
    __tablename__ = 'users'
    __table_args__ = {"schema": schema_Name}
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # Auth0 sub (subject) identifier - this is how we link to Auth0 users
    auth0_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile: Mapped[Optional["ProfileModel"]] = relationship("ProfileModel", back_populates="user", uselist=False)
    matches: Mapped[List["MatchModel"]] = relationship("MatchModel", back_populates="user")
    match_requests: Mapped[List["MatchRequestModel"]] = relationship("MatchRequestModel", back_populates="user")
    notifications: Mapped[List["NotificationModel"]] = relationship("NotificationModel", back_populates="recipient_user")
    volunteer_history: Mapped[List["VolunteerHistoryEntryModel"]] = relationship("VolunteerHistoryEntryModel", back_populates="user")

class ProfileModel(Base):
    __tablename__ = 'profiles'
    __table_args__ = {"schema": schema_Name}
    
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list)  # Store as JSON array
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)    # Store as JSON array
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="profile")
    availability: Mapped[List["AvailabilityWindowModel"]] = relationship("AvailabilityWindowModel", back_populates="profile", cascade="all, delete-orphan")

class AvailabilityWindowModel(Base):
    __tablename__ = 'availability_windows'
    __table_args__ = {"schema": schema_Name}
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('profiles.user_id'), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon ... 6=Sun
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    # Relationships
    profile: Mapped["ProfileModel"] = relationship("ProfileModel", back_populates="availability")
    
    __table_args__ = (
        Index('idx_availability_user_weekday', 'user_id', 'weekday'),
    )

class EventModel(Base):
    __tablename__ = 'events'
    __table_args__ = {"schema": schema_Name}

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[EventStatusEnum] = mapped_column(ENUM(EventStatusEnum), default=EventStatusEnum.DRAFT)
    required_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Location fields (denormalized for simplicity)
    location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location_postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    opportunities: Mapped[List["OpportunityModel"]] = relationship("OpportunityModel", back_populates="event", cascade="all, delete-orphan")
    volunteer_history: Mapped[List["VolunteerHistoryEntryModel"]] = relationship("VolunteerHistoryEntryModel", back_populates="event")
    
    __table_args__ = (
        Index('idx_events_starts_at', 'starts_at'),
        Index('idx_events_status', 'status'),
    )

class OpportunityModel(Base):
    __tablename__ = 'opportunities'
    __table_args__ = {"schema": schema_Name}
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    min_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_slots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    event: Mapped["EventModel"] = relationship("EventModel", back_populates="opportunities")
    matches: Mapped[List["MatchModel"]] = relationship("MatchModel", back_populates="opportunity")
    match_requests: Mapped[List["MatchRequestModel"]] = relationship("MatchRequestModel", back_populates="opportunity")
    
    __table_args__ = (
        Index('idx_opportunities_event_id', 'event_id'),
    )

class MatchModel(Base):
    __tablename__ = 'matches'
    __table_args__ = {"schema": schema_Name}
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    opportunity_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('opportunities.id'), nullable=False)
    status: Mapped[MatchStatusEnum] = mapped_column(ENUM(MatchStatusEnum), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="matches")
    opportunity: Mapped["OpportunityModel"] = relationship("OpportunityModel", back_populates="matches")
    
    __table_args__ = (
        Index('idx_matches_user_id', 'user_id'),
        Index('idx_matches_opportunity_id', 'opportunity_id'),
        Index('idx_matches_status', 'status'),
    )

class MatchRequestModel(Base):
    __tablename__ = 'match_requests'
    __table_args__ = {"schema": schema_Name}
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    opportunity_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('opportunities.id'), nullable=False)
    status: Mapped[MatchStatusEnum] = mapped_column(ENUM(MatchStatusEnum), default=MatchStatusEnum.PENDING)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="match_requests")
    opportunity: Mapped["OpportunityModel"] = relationship("OpportunityModel", back_populates="match_requests")
    
    __table_args__ = (
        Index('idx_match_requests_user_id', 'user_id'),
        Index('idx_match_requests_opportunity_id', 'opportunity_id'),
        Index('idx_match_requests_status', 'status'),
    )

class NotificationModel(Base):
    __tablename__ = 'notifications'
    __table_args__ = {"schema": schema_Name}
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    recipient_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[NotificationChannelEnum] = mapped_column(ENUM(NotificationChannelEnum), nullable=False)
    status: Mapped[NotificationStatusEnum] = mapped_column(ENUM(NotificationStatusEnum), default=NotificationStatusEnum.QUEUED)
    queued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    recipient_user: Mapped["UserModel"] = relationship("UserModel", back_populates="notifications")
    
    __table_args__ = (
        Index('idx_notifications_recipient_id', 'recipient_id'),
        Index('idx_notifications_status', 'status'),
        Index('idx_notifications_queued_at', 'queued_at'),
    )

class VolunteerHistoryEntryModel(Base):
    __tablename__ = 'volunteer_history'
    __table_args__ = {"schema": schema_Name}
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    event_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    hours: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="volunteer_history")
    event: Mapped["EventModel"] = relationship("EventModel", back_populates="volunteer_history")
    
    __table_args__ = (
        Index('idx_volunteer_history_user_id', 'user_id'),
        Index('idx_volunteer_history_event_id', 'event_id'),
        Index('idx_volunteer_history_date', 'date'),
    )