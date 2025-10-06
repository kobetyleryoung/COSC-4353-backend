from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from src.domain.volunteering import VolunteerHistoryEntry, VolunteerHistoryEntryId, Role
from src.domain.events import EventId
from src.domain.users import UserId
from config.logging_config import logger


class VolunteerHistoryService:
    """Service for tracking and displaying volunteer participation history."""
    
    def __init__(self):
        # Hard-coded data storage (no database implementation)
        self._history_entries: dict[str, VolunteerHistoryEntry] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self) -> None:
        """Initialize with sample volunteer history entries."""
        # Sample history entry 1
        user1_id = UserId.new()
        event1_id = EventId.new()
        entry1_id = VolunteerHistoryEntryId.new()
        entry1 = VolunteerHistoryEntry(
            id=entry1_id,
            user_id=user1_id,
            event_id=event1_id,
            role="General Volunteer",
            hours=4.5,
            date=datetime.now() - timedelta(days=30),
            notes="Helped with park cleanup, very organized event"
        )
        self._history_entries[str(entry1_id.value)] = entry1
        
        # Sample history entry 2
        user2_id = UserId.new()
        event2_id = EventId.new()
        entry2_id = VolunteerHistoryEntryId.new()
        entry2 = VolunteerHistoryEntry(
            id=entry2_id,
            user_id=user2_id,
            event_id=event2_id,
            role="Team Leader",
            hours=6.0,
            date=datetime.now() - timedelta(days=45),
            notes="Led a team of 5 volunteers in food distribution"
        )
        self._history_entries[str(entry2_id.value)] = entry2
        
        # Sample history entry 3 (same user as entry1, different event)
        event3_id = EventId.new()
        entry3_id = VolunteerHistoryEntryId.new()
        entry3 = VolunteerHistoryEntry(
            id=entry3_id,
            user_id=user1_id,  # Same user as entry1
            event_id=event3_id,
            role="Assistant",
            hours=3.0,
            date=datetime.now() - timedelta(days=60),
            notes="Assisted with senior center activities"
        )
        self._history_entries[str(entry3_id.value)] = entry3
        
        # Sample history entry 4
        user3_id = UserId.new()
        event4_id = EventId.new()
        entry4_id = VolunteerHistoryEntryId.new()
        entry4 = VolunteerHistoryEntry(
            id=entry4_id,
            user_id=user3_id,
            event_id=event4_id,
            role="Coordinator",
            hours=8.0,
            date=datetime.now() - timedelta(days=15),
            notes="Coordinated logistics for community health fair"
        )
        self._history_entries[str(entry4_id.value)] = entry4
        
        logger.info(f"Initialized {len(self._history_entries)} sample volunteer history entries")
    
    def create_history_entry(
        self,
        user_id: UserId,
        event_id: EventId,
        role: Role,
        hours: float,
        date: datetime,
        notes: Optional[str] = None
    ) -> VolunteerHistoryEntry:
        """Create a new volunteer history entry."""
        # Validation
        if not role or len(role.strip()) == 0:
            raise ValueError("Role is required")
        if len(role) > 100:
            raise ValueError("Role must be 100 characters or less")
        
        if hours <= 0:
            raise ValueError("Hours must be greater than 0")
        if hours > 24:
            raise ValueError("Hours cannot exceed 24 for a single entry")
        
        if date > datetime.now():
            raise ValueError("Date cannot be in the future")
        
        if notes and len(notes) > 1000:
            raise ValueError("Notes must be 1000 characters or less")
        
        # Check for duplicate entry (same user, event, and date)
        existing_entry = self._find_existing_entry(user_id, event_id, date)
        if existing_entry:
            raise ValueError("History entry already exists for this user, event, and date")
        
        # Create history entry
        entry_id = VolunteerHistoryEntryId.new()
        entry = VolunteerHistoryEntry(
            id=entry_id,
            user_id=user_id,
            event_id=event_id,
            role=role.strip(),
            hours=hours,
            date=date,
            notes=notes.strip() if notes else None
        )
        
        self._history_entries[str(entry_id.value)] = entry
        logger.info(f"Created history entry for user {user_id.value}, event {event_id.value}")
        
        return entry
    
    def get_history_entry_by_id(self, entry_id: VolunteerHistoryEntryId) -> Optional[VolunteerHistoryEntry]:
        """Retrieve a history entry by its ID."""
        return self._history_entries.get(str(entry_id.value))
    
    def get_user_history(self, user_id: UserId) -> List[VolunteerHistoryEntry]:
        """Get all volunteer history entries for a specific user."""
        user_entries = [
            entry for entry in self._history_entries.values()
            if entry.user_id.value == user_id.value
        ]
        
        # Sort by date (most recent first)
        user_entries.sort(key=lambda x: x.date, reverse=True)
        return user_entries
    
    def get_event_history(self, event_id: EventId) -> List[VolunteerHistoryEntry]:
        """Get all volunteer history entries for a specific event."""
        event_entries = [
            entry for entry in self._history_entries.values()
            if entry.event_id.value == event_id.value
        ]
        
        # Sort by date (most recent first)
        event_entries.sort(key=lambda x: x.date, reverse=True)
        return event_entries
    
    def get_user_total_hours(self, user_id: UserId) -> float:
        """Calculate total volunteer hours for a user."""
        user_entries = self.get_user_history(user_id)
        return sum(entry.hours for entry in user_entries)
    
    def get_user_hours_in_period(
        self,
        user_id: UserId,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate volunteer hours for a user within a specific time period."""
        if start_date > end_date:
            raise ValueError("Start date must be before end date")
        
        user_entries = self.get_user_history(user_id)
        period_entries = [
            entry for entry in user_entries
            if start_date <= entry.date <= end_date
        ]
        
        return sum(entry.hours for entry in period_entries)
    
    def get_user_event_count(self, user_id: UserId) -> int:
        """Get the number of unique events a user has volunteered for."""
        user_entries = self.get_user_history(user_id)
        unique_events = set(entry.event_id.value for entry in user_entries)
        return len(unique_events)
    
    def get_user_roles(self, user_id: UserId) -> List[str]:
        """Get all unique roles a user has performed."""
        user_entries = self.get_user_history(user_id)
        unique_roles = list(set(entry.role for entry in user_entries))
        return sorted(unique_roles)
    
    def get_recent_history(self, days: int = 30) -> List[VolunteerHistoryEntry]:
        """Get volunteer history entries from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = [
            entry for entry in self._history_entries.values()
            if entry.date >= cutoff_date
        ]
        
        # Sort by date (most recent first)
        recent_entries.sort(key=lambda x: x.date, reverse=True)
        return recent_entries
    
    def get_top_volunteers_by_hours(self, limit: int = 10) -> List[tuple[UserId, float]]:
        """Get top volunteers by total hours volunteered."""
        user_hours = {}
        
        for entry in self._history_entries.values():
            user_id = entry.user_id
            if user_id not in user_hours:
                user_hours[user_id] = 0
            user_hours[user_id] += entry.hours
        
        # Sort by hours (descending) and limit results
        sorted_volunteers = sorted(user_hours.items(), key=lambda x: x[1], reverse=True)
        return sorted_volunteers[:limit]
    
    def get_top_volunteers_by_events(self, limit: int = 10) -> List[tuple[UserId, int]]:
        """Get top volunteers by number of events participated in."""
        user_events = {}
        
        for entry in self._history_entries.values():
            user_id = entry.user_id
            if user_id not in user_events:
                user_events[user_id] = set()
            user_events[user_id].add(entry.event_id.value)
        
        # Convert sets to counts and sort
        user_event_counts = [(user_id, len(events)) for user_id, events in user_events.items()]
        sorted_volunteers = sorted(user_event_counts, key=lambda x: x[1], reverse=True)
        return sorted_volunteers[:limit]
    
    def update_history_entry(
        self,
        entry_id: VolunteerHistoryEntryId,
        role: Optional[Role] = None,
        hours: Optional[float] = None,
        date: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Optional[VolunteerHistoryEntry]:
        """Update an existing history entry."""
        entry = self.get_history_entry_by_id(entry_id)
        if not entry:
            return None
        
        # Validation for updates
        if role is not None:
            if not role or len(role.strip()) == 0:
                raise ValueError("Role cannot be empty")
            if len(role) > 100:
                raise ValueError("Role must be 100 characters or less")
            entry.role = role.strip()
        
        if hours is not None:
            if hours <= 0:
                raise ValueError("Hours must be greater than 0")
            if hours > 24:
                raise ValueError("Hours cannot exceed 24 for a single entry")
            entry.hours = hours
        
        if date is not None:
            if date > datetime.now():
                raise ValueError("Date cannot be in the future")
            entry.date = date
        
        if notes is not None:
            if notes and len(notes) > 1000:
                raise ValueError("Notes must be 1000 characters or less")
            entry.notes = notes.strip() if notes else None
        
        logger.info(f"Updated history entry {entry_id.value}")
        return entry
    
    def delete_history_entry(self, entry_id: VolunteerHistoryEntryId) -> bool:
        """Delete a volunteer history entry."""
        if str(entry_id.value) not in self._history_entries:
            return False
        
        entry = self._history_entries.pop(str(entry_id.value))
        logger.info(f"Deleted history entry {entry_id.value} for user {entry.user_id.value}")
        return True
    
    def get_volunteer_statistics(self, user_id: UserId) -> dict:
        """Get comprehensive volunteer statistics for a user."""
        user_entries = self.get_user_history(user_id)
        
        if not user_entries:
            return {
                "total_hours": 0,
                "total_events": 0,
                "unique_roles": 0,
                "first_volunteer_date": None,
                "last_volunteer_date": None,
                "average_hours_per_event": 0,
                "most_common_role": None
            }
        
        total_hours = sum(entry.hours for entry in user_entries)
        unique_events = len(set(entry.event_id.value for entry in user_entries))
        unique_roles = len(set(entry.role for entry in user_entries))
        
        dates = [entry.date for entry in user_entries]
        first_date = min(dates)
        last_date = max(dates)
        
        # Calculate most common role
        role_counts = {}
        for entry in user_entries:
            role_counts[entry.role] = role_counts.get(entry.role, 0) + 1
        most_common_role = max(role_counts.items(), key=lambda x: x[1])[0] if role_counts else None
        
        return {
            "total_hours": total_hours,
            "total_events": unique_events,
            "unique_roles": unique_roles,
            "first_volunteer_date": first_date,
            "last_volunteer_date": last_date,
            "average_hours_per_event": total_hours / unique_events if unique_events > 0 else 0,
            "most_common_role": most_common_role
        }
    
    def get_monthly_volunteer_hours(self, user_id: UserId, year: int) -> dict[int, float]:
        """Get volunteer hours by month for a specific year."""
        user_entries = self.get_user_history(user_id)
        monthly_hours = {month: 0.0 for month in range(1, 13)}
        
        for entry in user_entries:
            if entry.date.year == year:
                monthly_hours[entry.date.month] += entry.hours
        
        return monthly_hours
    
    def _find_existing_entry(
        self,
        user_id: UserId,
        event_id: EventId,
        date: datetime
    ) -> Optional[VolunteerHistoryEntry]:
        """Find if an entry already exists for the same user, event, and date."""
        for entry in self._history_entries.values():
            if (entry.user_id.value == user_id.value and
                entry.event_id.value == event_id.value and
                entry.date.date() == date.date()):  # Compare just the date part
                return entry
        return None
