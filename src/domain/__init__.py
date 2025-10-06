# domain/__init__.py
from .auth import AuthSession, AuthProvider
from .events import Event, EventId, EventStatus, Location
from .notifications import Notification, NotificationChannel, NotificationStatus, NotificationId
from .profiles import Profile, UserId, Skill, AvailabilityWindow
from .volunteering import (
    Opportunity, OpportunityId, MatchRequest, MatchRequestId, MatchStatus,
    Match, MatchId, VolunteerHistoryEntry, VolunteerHistoryEntryId, Role
)
from .users import User, UserRole
