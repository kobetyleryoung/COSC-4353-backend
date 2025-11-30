"""
Repository implementations using SQLAlchemy.

These classes implement the repository protocols defined in domain.repositories
and handle mapping between domain models and SQLAlchemy database models.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..domain.repositories import (
    EventRepository, ProfileRepository, OpportunityRepository,
    MatchRepository, MatchRequestRepository, NotificationRepository,
    UserRepository
)
from ..domain.events import Event, EventId, Location, EventStatus
from ..domain.profiles import Profile, AvailabilityWindow
from ..domain.volunteering import (
    Opportunity, OpportunityId, Match, MatchId, MatchRequest, MatchRequestId,
    VolunteerHistoryEntry, VolunteerHistoryEntryId, MatchStatus
)
from ..domain.notifications import Notification, NotificationId, NotificationChannel, NotificationStatus
from ..domain.users import User, UserId, UserRole
from .models import (
    EventModel, ProfileModel, OpportunityModel, MatchModel, MatchRequestModel,
    NotificationModel, UserModel, AvailabilityWindowModel, VolunteerHistoryEntryModel,
    UserRoleEnum, EventStatusEnum, NotificationChannelEnum, NotificationStatusEnum,
    MatchStatusEnum, user_roles
)

def _map_user_role_to_enum(role: UserRole) -> UserRoleEnum:
    """Map domain UserRole to database enum."""
    mapping = {
        UserRole.ADMIN: UserRoleEnum.ADMIN,
        UserRole.ORGANIZER: UserRoleEnum.ORGANIZER,
        UserRole.VOLUNTEER: UserRoleEnum.VOLUNTEER,
    }
    return mapping[role]

def _map_enum_to_user_role(enum_val: UserRoleEnum) -> UserRole:
    """Map database enum to domain UserRole."""
    mapping = {
        UserRoleEnum.ADMIN: UserRole.ADMIN,
        UserRoleEnum.ORGANIZER: UserRole.ORGANIZER,
        UserRoleEnum.VOLUNTEER: UserRole.VOLUNTEER,
    }
    return mapping[enum_val]

def _map_event_status_to_enum(status: EventStatus) -> EventStatusEnum:
    """Map domain EventStatus to database enum."""
    mapping = {
        EventStatus.DRAFT: EventStatusEnum.DRAFT,
        EventStatus.PUBLISHED: EventStatusEnum.PUBLISHED,
        EventStatus.CANCELLED: EventStatusEnum.CANCELLED,
    }
    return mapping[status]

def _map_enum_to_event_status(enum_val: EventStatusEnum) -> EventStatus:
    """Map database enum to domain EventStatus."""
    mapping = {
        EventStatusEnum.DRAFT: EventStatus.DRAFT,
        EventStatusEnum.PUBLISHED: EventStatus.PUBLISHED,
        EventStatusEnum.CANCELLED: EventStatus.CANCELLED,
    }
    return mapping[enum_val]

def _map_notification_channel_to_enum(channel: NotificationChannel) -> NotificationChannelEnum:
    """Map domain NotificationChannel to database enum."""
    mapping = {
        NotificationChannel.EMAIL: NotificationChannelEnum.EMAIL,
        NotificationChannel.SMS: NotificationChannelEnum.SMS,
        NotificationChannel.PUSH: NotificationChannelEnum.PUSH,
        NotificationChannel.IN_APP: NotificationChannelEnum.IN_APP,
    }
    return mapping[channel]

def _map_enum_to_notification_channel(enum_val: NotificationChannelEnum) -> NotificationChannel:
    """Map database enum to domain NotificationChannel."""
    mapping = {
        NotificationChannelEnum.EMAIL: NotificationChannel.EMAIL,
        NotificationChannelEnum.SMS: NotificationChannel.SMS,
        NotificationChannelEnum.PUSH: NotificationChannel.PUSH,
        NotificationChannelEnum.IN_APP: NotificationChannel.IN_APP,
    }
    return mapping[enum_val]

def _map_notification_status_to_enum(status: NotificationStatus) -> NotificationStatusEnum:
    """Map domain NotificationStatus to database enum."""
    mapping = {
        NotificationStatus.QUEUED: NotificationStatusEnum.QUEUED,
        NotificationStatus.SENT: NotificationStatusEnum.SENT,
        NotificationStatus.FAILED: NotificationStatusEnum.FAILED,
    }
    return mapping[status]

def _map_enum_to_notification_status(enum_val: NotificationStatusEnum) -> NotificationStatus:
    """Map database enum to domain NotificationStatus."""
    mapping = {
        NotificationStatusEnum.QUEUED: NotificationStatus.QUEUED,
        NotificationStatusEnum.SENT: NotificationStatus.SENT,
        NotificationStatusEnum.FAILED: NotificationStatus.FAILED,
    }
    return mapping[enum_val]

def _map_match_status_to_enum(status: MatchStatus) -> MatchStatusEnum:
    """Map domain MatchStatus to database enum."""
    mapping = {
        MatchStatus.PENDING: MatchStatusEnum.PENDING,
        MatchStatus.ACCEPTED: MatchStatusEnum.ACCEPTED,
        MatchStatus.REJECTED: MatchStatusEnum.REJECTED,
        MatchStatus.EXPIRED: MatchStatusEnum.EXPIRED,
    }
    return mapping[status]

def _map_enum_to_match_status(enum_val: MatchStatusEnum) -> MatchStatus:
    """Map database enum to domain MatchStatus."""
    mapping = {
        MatchStatusEnum.PENDING: MatchStatus.PENDING,
        MatchStatusEnum.ACCEPTED: MatchStatus.ACCEPTED,
        MatchStatusEnum.REJECTED: MatchStatus.REJECTED,
        MatchStatusEnum.EXPIRED: MatchStatus.EXPIRED,
    }
    return mapping[enum_val]

class SqlAlchemyUserRepository:
    """SQLAlchemy implementation of UserRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, user_id: UserId) -> Optional[User]:
        """Get user by ID."""
        user_model = self.session.query(UserModel).filter_by(id=user_id.value).first()
        if not user_model:
            return None
        return self._model_to_domain(user_model)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        user_model = self.session.query(UserModel).filter_by(email=email).first()
        if not user_model:
            return None
        return self._model_to_domain(user_model)
    
    def get_by_auth0_sub(self, auth0_sub: str) -> Optional[User]:
        """Get user by Auth0 subject identifier."""
        user_model = self.session.query(UserModel).filter_by(auth0_sub=auth0_sub).first()
        if not user_model:
            return None
        return self._model_to_domain(user_model)
    
    def add(self, user: User) -> None:
        """Add a new user."""
        user_model = self._domain_to_model(user)
        self.session.add(user_model)
    
    def save(self, user: User) -> None:
        """Save/update an existing user."""
        user_model = self.session.query(UserModel).filter_by(id=user.id.value).first()
        if user_model:
            # Update existing
            user_model.email = user.email
            user_model.auth0_sub = user.auth0_sub
            
            # Update roles
            self.session.execute(user_roles.delete().where(user_roles.c.user_id == user.id.value))
            for role in user.roles:
                self.session.execute(user_roles.insert().values(
                    user_id=user.id.value,
                    role=_map_user_role_to_enum(role)
                ))
        else:
            # Add new
            self.add(user)
    
    def _domain_to_model(self, user: User) -> UserModel:
        """Convert domain User to UserModel."""
        user_model = UserModel(
            id=user.id.value,
            email=user.email,
            auth0_sub=user.auth0_sub
        )
        return user_model
    
    def _model_to_domain(self, user_model: UserModel) -> User:
        """Convert UserModel to domain User."""
        # Get user roles
        role_results = self.session.execute(
            user_roles.select().where(user_roles.c.user_id == user_model.id)
        ).fetchall()
        
        roles = {_map_enum_to_user_role(row.role) for row in role_results}
        
        return User(
            id=UserId(user_model.id),
            email=user_model.email,
            roles=roles,
            auth0_sub=user_model.auth0_sub
        )

class SqlAlchemyProfileRepository:
    """SQLAlchemy implementation of ProfileRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, user_id: UserId) -> Optional[Profile]:
        """Get profile by user ID."""
        profile_model = self.session.query(ProfileModel).filter_by(user_id=user_id.value).first()
        if not profile_model:
            return None
        return self._model_to_domain(profile_model)
    
    def save(self, profile: Profile) -> None:
        """Save/update a profile."""
        profile_model = self.session.query(ProfileModel).filter_by(user_id=profile.user_id.value).first()
        if profile_model:
            # Update existing
            profile_model.display_name = profile.display_name
            profile_model.phone = profile.phone
            profile_model.skills = profile.skills
            profile_model.tags = profile.tags
            profile_model.updated_at = profile.updated_at
            
            # Delete and recreate availability windows
            self.session.query(AvailabilityWindowModel).filter_by(user_id=profile.user_id.value).delete()
            for window in profile.availability:
                window_model = AvailabilityWindowModel(
                    user_id=profile.user_id.value,
                    weekday=window.weekday,
                    start_time=window.start,
                    end_time=window.end
                )
                self.session.add(window_model)
        else:
            # Add new
            profile_model = self._domain_to_model(profile)
            self.session.add(profile_model)
            
            # Add availability windows
            for window in profile.availability:
                window_model = AvailabilityWindowModel(
                    user_id=profile.user_id.value,
                    weekday=window.weekday,
                    start_time=window.start,
                    end_time=window.end
                )
                self.session.add(window_model)
    
    def _domain_to_model(self, profile: Profile) -> ProfileModel:
        """Convert domain Profile to ProfileModel."""
        return ProfileModel(
            user_id=profile.user_id.value,
            display_name=profile.display_name,
            phone=profile.phone,
            skills=profile.skills,
            tags=profile.tags,
            updated_at=profile.updated_at
        )
    
    def _model_to_domain(self, profile_model: ProfileModel) -> Profile:
        """Convert ProfileModel to domain Profile."""
        # Get availability windows
        windows = self.session.query(AvailabilityWindowModel).filter_by(
            user_id=profile_model.user_id
        ).all()
        
        availability = [
            AvailabilityWindow(
                weekday=window.weekday,
                start=window.start_time,
                end=window.end_time
            )
            for window in windows
        ]
        
        return Profile(
            user_id=UserId(profile_model.user_id),
            display_name=profile_model.display_name,
            phone=profile_model.phone,
            skills=profile_model.skills or [],
            tags=profile_model.tags or [],
            availability=availability,
            updated_at=profile_model.updated_at
        )

class SqlAlchemyEventRepository:
    """SQLAlchemy implementation of EventRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, event_id: EventId) -> Optional[Event]:
        """Get event by ID."""
        event_model = self.session.query(EventModel).filter_by(id=event_id.value).first()
        if not event_model:
            return None
        return self._model_to_domain(event_model)
    
    def add(self, event: Event) -> None:
        """Add a new event."""
        event_model = self._domain_to_model(event)
        self.session.add(event_model)
    
    def save(self, event: Event) -> None:
        """Save/update an existing event."""
        event_model = self.session.query(EventModel).filter_by(id=event.id.value).first()
        if event_model:
            # Update existing
            event_model.title = event.title
            event_model.description = event.description
            event_model.starts_at = event.starts_at
            event_model.ends_at = event.ends_at
            event_model.capacity = event.capacity
            event_model.status = _map_event_status_to_enum(event.status)
            event_model.required_skills = event.required_skills
            
            # Update location
            if event.location:
                event_model.location_name = event.location.name
                event_model.location_address = event.location.address
                event_model.location_city = event.location.city
                event_model.location_state = event.location.state
                event_model.location_postal_code = event.location.postal_code
            else:
                event_model.location_name = None
                event_model.location_address = None
                event_model.location_city = None
                event_model.location_state = None
                event_model.location_postal_code = None
        else:
            # Add new
            self.add(event)
    
    def get_by_id(self, event_id: EventId) -> Optional[Event]:
        """Get event by ID (alias for get)."""
        return self.get(event_id)
    
    def list_all(self) -> list[Event]:
        """List all events."""
        event_models = self.session.query(EventModel).all()
        return [self._model_to_domain(model) for model in event_models]
    
    def list_by_status(self, status: EventStatus) -> list[Event]:
        """List events by status."""
        status_enum = _map_event_status_to_enum(status)
        event_models = (
            self.session.query(EventModel)
            .filter(EventModel.status == status_enum)
            .all()
        )
        return [self._model_to_domain(model) for model in event_models]
    
    def list_upcoming(self, *, limit: int = 50, as_of: datetime | None = None) -> list[Event]:
        """List upcoming events."""
        if as_of is None:
            as_of = datetime.now()
        
        event_models = (
            self.session.query(EventModel)
            .filter(EventModel.starts_at >= as_of)
            .filter(EventModel.status == EventStatusEnum.PUBLISHED)
            .order_by(EventModel.starts_at)
            .limit(limit)
            .all()
        )
        
        return [self._model_to_domain(model) for model in event_models]
    
    def _domain_to_model(self, event: Event) -> EventModel:
        """Convert domain Event to EventModel."""
        model = EventModel(
            id=event.id.value,
            title=event.title,
            description=event.description,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            capacity=event.capacity,
            status=_map_event_status_to_enum(event.status),
            required_skills=event.required_skills
        )
        
        if event.location:
            model.location_name = event.location.name
            model.location_address = event.location.address
            model.location_city = event.location.city
            model.location_state = event.location.state
            model.location_postal_code = event.location.postal_code
        
        return model
    
    def _model_to_domain(self, event_model: EventModel) -> Event:
        """Convert EventModel to domain Event."""
        location = None
        if event_model.location_name:
            location = Location(
                name=event_model.location_name,
                address=event_model.location_address,
                city=event_model.location_city,
                state=event_model.location_state,
                postal_code=event_model.location_postal_code
            )
        
        return Event(
            id=EventId(event_model.id),
            title=event_model.title,
            starts_at=event_model.starts_at,
            ends_at=event_model.ends_at,
            location=location,
            description=event_model.description,
            capacity=event_model.capacity,
            status=_map_enum_to_event_status(event_model.status),
            required_skills=event_model.required_skills or []
        )

class SqlAlchemyOpportunityRepository:
    """SQLAlchemy implementation of OpportunityRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, opp_id: OpportunityId) -> Optional[Opportunity]:
        """Get opportunity by ID."""
        opp_model = self.session.query(OpportunityModel).filter_by(id=opp_id.value).first()
        if not opp_model:
            return None
        return self._model_to_domain(opp_model)
    
    def add(self, opp: Opportunity) -> None:
        """Add a new opportunity."""
        opp_model = self._domain_to_model(opp)
        self.session.add(opp_model)
    
    def save(self, opp: Opportunity) -> None:
        """Save/update an existing opportunity."""
        opp_model = self.session.query(OpportunityModel).filter_by(id=opp.id.value).first()
        if opp_model:
            # Update existing
            opp_model.event_id = opp.event_id.value
            opp_model.title = opp.title
            opp_model.description = opp.description
            opp_model.required_skills = opp.required_skills
            opp_model.min_hours = opp.min_hours
            opp_model.max_slots = opp.max_slots
        else:
            # Add new
            self.add(opp)
    
    def list_for_event(self, event_id: EventId) -> list[Opportunity]:
        """List all opportunities for an event."""
        opp_models = (
            self.session.query(OpportunityModel)
            .filter_by(event_id=event_id.value)
            .all()
        )
        return [self._model_to_domain(model) for model in opp_models]
    
    def list_all(self, *, limit: int = 100) -> list[Opportunity]:
        """List all opportunities."""
        opp_models = (
            self.session.query(OpportunityModel)
            .limit(limit)
            .all()
        )
        return [self._model_to_domain(model) for model in opp_models]
    
    def _domain_to_model(self, opp: Opportunity) -> OpportunityModel:
        """Convert domain Opportunity to OpportunityModel."""
        return OpportunityModel(
            id=opp.id.value,
            event_id=opp.event_id.value,
            title=opp.title,
            description=opp.description,
            required_skills=opp.required_skills,
            min_hours=opp.min_hours,
            max_slots=opp.max_slots
        )
    
    def _model_to_domain(self, opp_model: OpportunityModel) -> Opportunity:
        """Convert OpportunityModel to domain Opportunity."""
        return Opportunity(
            id=OpportunityId(opp_model.id),
            event_id=EventId(opp_model.event_id),
            title=opp_model.title,
            description=opp_model.description,
            required_skills=opp_model.required_skills or [],
            min_hours=opp_model.min_hours,
            max_slots=opp_model.max_slots
        )

class SqlAlchemyMatchRepository:
    """SQLAlchemy implementation of MatchRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, match_id: MatchId) -> Optional[Match]:
        """Get match by ID."""
        match_model = self.session.query(MatchModel).filter_by(id=match_id.value).first()
        if not match_model:
            return None
        return self._model_to_domain(match_model)
    
    def add(self, match: Match) -> None:
        """Add a new match."""
        match_model = self._domain_to_model(match)
        self.session.add(match_model)
    
    def save(self, match: Match) -> None:
        """Save/update an existing match."""
        match_model = self.session.query(MatchModel).filter_by(id=match.id.value).first()
        if match_model:
            # Update existing
            match_model.user_id = match.user_id.value
            match_model.opportunity_id = match.opportunity_id.value
            match_model.status = _map_match_status_to_enum(match.status)
            match_model.score = match.score
            match_model.created_at = match.created_at
        else:
            # Add new
            self.add(match)
    
    def list_for_user(self, user_id: UserId, *, limit: int = 100) -> list[Match]:
        """List matches for a user."""
        match_models = (
            self.session.query(MatchModel)
            .filter_by(user_id=user_id.value)
            .order_by(MatchModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._model_to_domain(model) for model in match_models]
    
    def list_for_opportunity(self, opp_id: OpportunityId) -> list[Match]:
        """List matches for an opportunity."""
        match_models = (
            self.session.query(MatchModel)
            .filter_by(opportunity_id=opp_id.value)
            .all()
        )
        return [self._model_to_domain(model) for model in match_models]
    
    def _domain_to_model(self, match: Match) -> MatchModel:
        """Convert domain Match to MatchModel."""
        return MatchModel(
            id=match.id.value,
            user_id=match.user_id.value,
            opportunity_id=match.opportunity_id.value,
            status=_map_match_status_to_enum(match.status),
            score=match.score,
            created_at=match.created_at
        )
    
    def _model_to_domain(self, match_model: MatchModel) -> Match:
        """Convert MatchModel to domain Match."""
        return Match(
            id=MatchId(match_model.id),
            user_id=UserId(match_model.user_id),
            opportunity_id=OpportunityId(match_model.opportunity_id),
            created_at=match_model.created_at,
            status=_map_enum_to_match_status(match_model.status),
            score=match_model.score
        )

class SqlAlchemyMatchRequestRepository:
    """SQLAlchemy implementation of MatchRequestRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, req_id: MatchRequestId) -> Optional[MatchRequest]:
        """Get match request by ID."""
        req_model = self.session.query(MatchRequestModel).filter_by(id=req_id.value).first()
        if not req_model:
            return None
        return self._model_to_domain(req_model)
    
    def add(self, req: MatchRequest) -> None:
        """Add a new match request."""
        req_model = self._domain_to_model(req)
        self.session.add(req_model)
    
    def save(self, req: MatchRequest) -> None:
        """Save/update an existing match request."""
        req_model = self.session.query(MatchRequestModel).filter_by(id=req.id.value).first()
        if req_model:
            # Update existing
            req_model.user_id = req.user_id.value
            req_model.opportunity_id = req.opportunity_id.value
            req_model.status = _map_match_status_to_enum(req.status)
            req_model.score = req.score
            req_model.requested_at = req.requested_at
        else:
            # Add new
            self.add(req)
    
    def list_pending_for_opportunity(self, opp_id: OpportunityId) -> list[MatchRequest]:
        """List pending match requests for an opportunity."""
        req_models = (
            self.session.query(MatchRequestModel)
            .filter_by(opportunity_id=opp_id.value, status=MatchStatusEnum.PENDING)
            .order_by(MatchRequestModel.requested_at)
            .all()
        )
        return [self._model_to_domain(model) for model in req_models]
    
    def list_for_user(self, user_id: UserId, *, limit: int = 100) -> list[MatchRequest]:
        """List match requests for a user."""
        req_models = (
            self.session.query(MatchRequestModel)
            .filter_by(user_id=user_id.value)
            .order_by(MatchRequestModel.requested_at.desc())
            .limit(limit)
            .all()
        )
        return [self._model_to_domain(model) for model in req_models]
    
    def find_by_user_and_opportunity(self, user_id: UserId, opp_id: OpportunityId) -> Optional[MatchRequest]:
        """Find a match request by user and opportunity."""
        req_model = (
            self.session.query(MatchRequestModel)
            .filter_by(user_id=user_id.value, opportunity_id=opp_id.value)
            .order_by(MatchRequestModel.requested_at.desc())
            .first()
        )
        if not req_model:
            return None
        return self._model_to_domain(req_model)
    
    def _domain_to_model(self, req: MatchRequest) -> MatchRequestModel:
        """Convert domain MatchRequest to MatchRequestModel."""
        return MatchRequestModel(
            id=req.id.value,
            user_id=req.user_id.value,
            opportunity_id=req.opportunity_id.value,
            status=_map_match_status_to_enum(req.status),
            score=req.score,
            requested_at=req.requested_at
        )
    
    def _model_to_domain(self, req_model: MatchRequestModel) -> MatchRequest:
        """Convert MatchRequestModel to domain MatchRequest."""
        return MatchRequest(
            id=MatchRequestId(req_model.id),
            user_id=UserId(req_model.user_id),
            opportunity_id=OpportunityId(req_model.opportunity_id),
            requested_at=req_model.requested_at,
            status=_map_enum_to_match_status(req_model.status),
            score=req_model.score
        )

class SqlAlchemyNotificationRepository:
    """SQLAlchemy implementation of NotificationRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, notif_id: NotificationId) -> Optional[Notification]:
        """Get notification by ID."""
        notif_model = self.session.query(NotificationModel).filter_by(id=notif_id.value).first()
        if not notif_model:
            return None
        return self._model_to_domain(notif_model)
    
    def add(self, notif: Notification) -> None:
        """Add a new notification."""
        notif_model = self._domain_to_model(notif)
        self.session.add(notif_model)
    
    def save(self, notif: Notification) -> None:
        """Save/update an existing notification."""
        notif_model = self.session.query(NotificationModel).filter_by(id=notif.id.value).first()
        if notif_model:
            # Update existing
            notif_model.recipient_id = notif.recipient.value
            notif_model.subject = notif.subject
            notif_model.body = notif.body
            notif_model.channel = _map_notification_channel_to_enum(notif.channel)
            notif_model.status = _map_notification_status_to_enum(notif.status)
            notif_model.queued_at = notif.queued_at
            notif_model.sent_at = notif.sent_at
            notif_model.error = notif.error
        else:
            # Add new
            self.add(notif)
    
    def list_queue(self, *, limit: int = 100) -> list[Notification]:
        """List queued notifications."""
        notif_models = (
            self.session.query(NotificationModel)
            .filter_by(status=NotificationStatusEnum.QUEUED)
            .order_by(NotificationModel.queued_at.asc())
            .limit(limit)
            .all()
        )
        return [self._model_to_domain(model) for model in notif_models]
    
    def get_by_user_id(
        self, 
        user_id: UserId, 
        *, 
        limit: Optional[int] = None,
        status_filter: Optional['NotificationStatus'] = None
    ) -> list[Notification]:
        """Get all notifications for a specific user."""
        from src.domain.notifications import NotificationStatus
        
        query = self.session.query(NotificationModel).filter_by(recipient_id=user_id.value)
        
        if status_filter:
            query = query.filter_by(status=_map_notification_status_to_enum(status_filter))
        
        query = query.order_by(NotificationModel.queued_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        notif_models = query.all()
        return [self._model_to_domain(model) for model in notif_models]
    
    def list_all(self, *, limit: int = 1000) -> list[Notification]:
        """List all notifications."""
        notif_models = (
            self.session.query(NotificationModel)
            .order_by(NotificationModel.queued_at.desc())
            .limit(limit)
            .all()
        )
        return [self._model_to_domain(model) for model in notif_models]
    
    def _domain_to_model(self, notif: Notification) -> NotificationModel:
        """Convert domain Notification to NotificationModel."""
        return NotificationModel(
            id=notif.id.value,
            recipient_id=notif.recipient.value,
            subject=notif.subject,
            body=notif.body,
            channel=_map_notification_channel_to_enum(notif.channel),
            status=_map_notification_status_to_enum(notif.status),
            queued_at=notif.queued_at,
            sent_at=notif.sent_at,
            error=notif.error
        )
    
    def _model_to_domain(self, notif_model: NotificationModel) -> Notification:
        """Convert NotificationModel to domain Notification."""
        return Notification(
            id=NotificationId(notif_model.id),
            recipient=UserId(notif_model.recipient_id),
            subject=notif_model.subject,
            body=notif_model.body,
            channel=_map_enum_to_notification_channel(notif_model.channel),
            status=_map_enum_to_notification_status(notif_model.status),
            queued_at=notif_model.queued_at,
            sent_at=notif_model.sent_at,
            error=notif_model.error
        )

class SqlAlchemyVolunteerHistoryRepository:
    """SQLAlchemy implementation of VolunteerHistoryRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, entry_id: VolunteerHistoryEntryId) -> Optional[VolunteerHistoryEntry]:
        """Get volunteer history entry by ID."""
        entry_model = self.session.query(VolunteerHistoryEntryModel).filter_by(id=entry_id.value).first()
        if not entry_model:
            return None
        return self._model_to_domain(entry_model)
    
    def add(self, entry: VolunteerHistoryEntry) -> None:
        """Add a new volunteer history entry."""
        entry_model = self._domain_to_model(entry)
        self.session.add(entry_model)
    
    def save(self, entry: VolunteerHistoryEntry) -> None:
        """Save/update an existing volunteer history entry."""
        entry_model = self.session.query(VolunteerHistoryEntryModel).filter_by(id=entry.id.value).first()
        if entry_model:
            # Update existing
            entry_model.user_id = entry.user_id.value
            entry_model.event_id = entry.event_id.value
            entry_model.role = entry.role
            entry_model.hours = entry.hours
            entry_model.date = entry.date
            entry_model.notes = entry.notes
        else:
            # Add new
            self.add(entry)
    
    def list_for_user(self, user_id: UserId, *, limit: int = 100) -> list[VolunteerHistoryEntry]:
        """List volunteer history entries for a user."""
        entry_models = (
            self.session.query(VolunteerHistoryEntryModel)
            .filter_by(user_id=user_id.value)
            .order_by(VolunteerHistoryEntryModel.date.desc())
            .limit(limit)
            .all()
        )
        return [self._model_to_domain(model) for model in entry_models]
    
    def list_for_event(self, event_id: EventId) -> list[VolunteerHistoryEntry]:
        """List volunteer history entries for an event."""
        entry_models = (
            self.session.query(VolunteerHistoryEntryModel)
            .filter_by(event_id=event_id.value)
            .all()
        )
        return [self._model_to_domain(model) for model in entry_models]
    
    def _domain_to_model(self, entry: VolunteerHistoryEntry) -> VolunteerHistoryEntryModel:
        """Convert domain VolunteerHistoryEntry to VolunteerHistoryEntryModel."""
        return VolunteerHistoryEntryModel(
            id=entry.id.value,
            user_id=entry.user_id.value,
            event_id=entry.event_id.value,
            role=entry.role,
            hours=entry.hours,
            date=entry.date,
            notes=entry.notes
        )
    
    def _model_to_domain(self, entry_model: VolunteerHistoryEntryModel) -> VolunteerHistoryEntry:
        """Convert VolunteerHistoryEntryModel to domain VolunteerHistoryEntry."""
        return VolunteerHistoryEntry(
            id=VolunteerHistoryEntryId(entry_model.id),
            user_id=UserId(entry_model.user_id),
            event_id=EventId(entry_model.event_id),
            role=entry_model.role,
            hours=entry_model.hours,
            date=entry_model.date,
            notes=entry_model.notes
        )