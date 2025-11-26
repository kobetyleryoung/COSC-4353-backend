from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
from logging import Logger

from src.domain.volunteering import VolunteerHistoryEntry, VolunteerHistoryEntryId, Role
from src.domain.events import EventId
from src.domain.users import UserId
from src.repositories.unit_of_work import UnitOfWorkManager


class VolunteerHistoryService:
    """Service for tracking and displaying volunteer participation history."""
    
    def __init__(self, uow_manager: UnitOfWorkManager, logger: Logger):
        self._uow_manager = uow_manager
        self._logger = logger
    
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
        
        with self._uow_manager.get_uow() as uow:
            uow.volunteer_history.add(entry)
            uow.commit()
        
        self._logger.info(f"Created history entry for user {user_id.value}, event {event_id.value}")
        return entry
    
    def get_history_entry_by_id(self, entry_id: VolunteerHistoryEntryId) -> Optional[VolunteerHistoryEntry]:
        """Retrieve a history entry by its ID."""
        with self._uow_manager.get_uow() as uow:
            return uow.volunteer_history.get_by_id(entry_id)
    
    def get_user_history(self, user_id: UserId) -> List[VolunteerHistoryEntry]:
        """Get all volunteer history entries for a specific user."""
        with self._uow_manager.get_uow() as uow:
            return uow.volunteer_history.get_by_user(user_id)
    
    def get_event_history(self, event_id: EventId) -> List[VolunteerHistoryEntry]:
        """Get all volunteer history entries for a specific event."""
        with self._uow_manager.get_uow() as uow:
            return uow.volunteer_history.get_by_event(event_id)
    
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
        with self._uow_manager.get_uow() as uow:
            all_entries = uow.volunteer_history.list_all()
            recent_entries = [
                entry for entry in all_entries
                if entry.date >= cutoff_date
            ]
            # Sort by date (most recent first)
            recent_entries.sort(key=lambda x: x.date, reverse=True)
            return recent_entries
    
    def get_top_volunteers_by_hours(self, limit: int = 10) -> List[tuple[UserId, float]]:
        """Get top volunteers by total hours volunteered."""
        with self._uow_manager.get_uow() as uow:
            all_entries = uow.volunteer_history.list_all()
            
        user_hours = {}
        for entry in all_entries:
            user_id = entry.user_id
            if user_id not in user_hours:
                user_hours[user_id] = 0
            user_hours[user_id] += entry.hours
        
        # Sort by hours (descending) and limit results
        sorted_volunteers = sorted(user_hours.items(), key=lambda x: x[1], reverse=True)
        return sorted_volunteers[:limit]
    
    def get_top_volunteers_by_events(self, limit: int = 10) -> List[tuple[UserId, int]]:
        """Get top volunteers by number of events participated in."""
        with self._uow_manager.get_uow() as uow:
            all_entries = uow.volunteer_history.list_all()
            
        user_events = {}
        for entry in all_entries:
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
        with self._uow_manager.get_uow() as uow:
            entry = uow.volunteer_history.get_by_id(entry_id)
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
            
            uow.volunteer_history.update(entry)
            uow.commit()
            
            self._logger.info(f"Updated history entry {entry_id.value}")
            return entry
    
    def delete_history_entry(self, entry_id: VolunteerHistoryEntryId) -> bool:
        """Delete a volunteer history entry."""
        with self._uow_manager.get_uow() as uow:
            entry = uow.volunteer_history.get_by_id(entry_id)
            if not entry:
                return False
            
            uow.volunteer_history.delete(entry_id)
            uow.commit()
            
            self._logger.info(f"Deleted history entry {entry_id.value} for user {entry.user_id.value}")
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
