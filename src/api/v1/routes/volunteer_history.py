from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID

from src.services.volunteer_history import VolunteerHistoryService
from src.domain.users import UserId
from src.domain.events import EventId
from src.domain.volunteering import VolunteerHistoryEntryId
from src.config.database_settings import get_uow
from src.repositories.unit_of_work import UnitOfWorkManager
from ..schemas.volunteer_history import (
    HistoryEntryCreateSchema, HistoryEntryUpdateSchema, HistoryEntryResponseSchema,
    HistoryListResponseSchema, UserStatsResponseSchema, TopVolunteerResponseSchema,
    MonthlyHoursResponseSchema, YearlyStatsResponseSchema
)
from src.config.logging_config import logger

router = APIRouter(prefix="/volunteer-history", tags=["volunteer-history"])

#region helpers

def _get_history_service(uow_manager: UnitOfWorkManager = Depends(get_uow)) -> VolunteerHistoryService:
    return VolunteerHistoryService(uow_manager, logger)


def _convert_history_entry_to_response(entry) -> HistoryEntryResponseSchema:
    """Convert domain VolunteerHistoryEntry to HistoryEntryResponseSchema."""
    return HistoryEntryResponseSchema(
        id=entry.id.value,
        user_id=entry.user_id.value,
        event_id=entry.event_id.value,
        role=entry.role,
        hours=entry.hours,
        date=entry.date,
        notes=entry.notes
    )

#endregion

@router.get("/", response_model=List[HistoryEntryResponseSchema])
async def get_recent_history(
    days: int = 30,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get recent volunteer history entries."""
    try:
        entries = history_service.get_recent_history(days)
        return [_convert_history_entry_to_response(entry) for entry in entries]
    except Exception as e:
        logger.error(f"Error getting recent history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent history"
        )


@router.get("/{entry_id}", response_model=HistoryEntryResponseSchema)
async def get_history_entry_by_id(
    entry_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get a specific history entry by ID."""
    try:
        entry = history_service.get_history_entry_by_id(VolunteerHistoryEntryId(entry_id))
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History entry not found"
            )
        
        return _convert_history_entry_to_response(entry)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history entry"
        )


@router.get("/user/{user_id}", response_model=HistoryListResponseSchema)
async def get_user_history(
    user_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get all volunteer history entries for a specific user."""
    try:
        entries = history_service.get_user_history(UserId(user_id))
        entry_responses = [_convert_history_entry_to_response(entry) for entry in entries]
        
        return HistoryListResponseSchema(
            entries=entry_responses,
            total=len(entry_responses)
        )
    except Exception as e:
        logger.error(f"Error getting user history for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user history"
        )


@router.get("/event/{event_id}", response_model=HistoryListResponseSchema)
async def get_event_history(
    event_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get all volunteer history entries for a specific event."""
    try:
        entries = history_service.get_event_history(EventId(event_id))
        entry_responses = [_convert_history_entry_to_response(entry) for entry in entries]
        
        return HistoryListResponseSchema(
            entries=entry_responses,
            total=len(entry_responses)
        )
    except Exception as e:
        logger.error(f"Error getting event history for {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event history"
        )


@router.post("/", response_model=HistoryEntryResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_history_entry(
    entry_data: HistoryEntryCreateSchema,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Create a new volunteer history entry."""
    try:
        # In real app, get user_id from authenticated user
        user_id = UserId.new()
        
        entry = history_service.create_history_entry(
            user_id=user_id,
            event_id=EventId(entry_data.event_id),
            role=entry_data.role,
            hours=entry_data.hours,
            date=entry_data.date,
            notes=entry_data.notes
        )
        
        return _convert_history_entry_to_response(entry)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error creating history entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create history entry"
        )


@router.put("/{entry_id}", response_model=HistoryEntryResponseSchema)
async def update_history_entry(
    entry_id: UUID,
    entry_data: HistoryEntryUpdateSchema,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Update an existing history entry."""
    try:
        entry = history_service.update_history_entry(
            entry_id=VolunteerHistoryEntryId(entry_id),
            role=entry_data.role,
            hours=entry_data.hours,
            date=entry_data.date,
            notes=entry_data.notes
        )
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History entry not found"
            )
        
        return _convert_history_entry_to_response(entry)
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error updating history entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update history entry"
        )


@router.delete("/{entry_id}")
async def delete_history_entry(
    entry_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Delete a volunteer history entry."""
    try:
        success = history_service.delete_history_entry(VolunteerHistoryEntryId(entry_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History entry not found"
            )
        
        return {"message": "History entry deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting history entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete history entry"
        )


@router.get("/user/{user_id}/total-hours", response_model=dict)
async def get_user_total_hours(
    user_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get total volunteer hours for a user."""
    try:
        total_hours = history_service.get_user_total_hours(UserId(user_id))
        return {"user_id": user_id, "total_hours": total_hours}
    except Exception as e:
        logger.error(f"Error getting total hours for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve total hours"
        )


@router.get("/user/{user_id}/hours-in-period", response_model=dict)
async def get_user_hours_in_period(
    user_id: UUID,
    start_date: str,
    end_date: str,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get volunteer hours for a user within a specific time period."""
    try:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        hours = history_service.get_user_hours_in_period(UserId(user_id), start_dt, end_dt)
        return {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "hours": hours
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error getting hours in period for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve hours in period"
        )


@router.get("/user/{user_id}/event-count", response_model=dict)
async def get_user_event_count(
    user_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get the number of unique events a user has volunteered for."""
    try:
        event_count = history_service.get_user_event_count(UserId(user_id))
        return {"user_id": user_id, "event_count": event_count}
    except Exception as e:
        logger.error(f"Error getting event count for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event count"
        )


@router.get("/user/{user_id}/roles", response_model=dict)
async def get_user_roles(
    user_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get all unique roles a user has performed."""
    try:
        roles = history_service.get_user_roles(UserId(user_id))
        return {"user_id": user_id, "roles": roles}
    except Exception as e:
        logger.error(f"Error getting roles for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user roles"
        )


@router.get("/user/{user_id}/statistics", response_model=UserStatsResponseSchema)
async def get_user_statistics(
    user_id: UUID,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get comprehensive volunteer statistics for a user."""
    try:
        stats = history_service.get_volunteer_statistics(UserId(user_id))
        return UserStatsResponseSchema(**stats)
    except Exception as e:
        logger.error(f"Error getting statistics for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/user/{user_id}/monthly-hours/{year}", response_model=YearlyStatsResponseSchema)
async def get_user_monthly_hours(
    user_id: UUID,
    year: int,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get volunteer hours by month for a specific year."""
    try:
        monthly_hours = history_service.get_monthly_volunteer_hours(UserId(user_id), year)
        
        monthly_responses = [
            MonthlyHoursResponseSchema(month=month, hours=hours)
            for month, hours in monthly_hours.items()
        ]
        
        total_hours = sum(monthly_hours.values())
        
        return YearlyStatsResponseSchema(
            year=year,
            monthly_hours=monthly_responses,
            total_hours=total_hours
        )
    except Exception as e:
        logger.error(f"Error getting monthly hours for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monthly hours"
        )


@router.get("/top-volunteers/by-hours", response_model=List[TopVolunteerResponseSchema])
async def get_top_volunteers_by_hours(
    limit: int = 10,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get top volunteers by total hours volunteered."""
    try:
        top_volunteers = history_service.get_top_volunteers_by_hours(limit)
        return [
            TopVolunteerResponseSchema(user_id=user_id.value, value=hours)
            for user_id, hours in top_volunteers
        ]
    except Exception as e:
        logger.error(f"Error getting top volunteers by hours: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top volunteers by hours"
        )


@router.get("/top-volunteers/by-events", response_model=List[TopVolunteerResponseSchema])
async def get_top_volunteers_by_events(
    limit: int = 10,
    history_service: VolunteerHistoryService = Depends(_get_history_service)
):
    """Get top volunteers by number of events participated in."""
    try:
        top_volunteers = history_service.get_top_volunteers_by_events(limit)
        return [
            TopVolunteerResponseSchema(user_id=user_id.value, value=float(event_count))
            for user_id, event_count in top_volunteers
        ]
    except Exception as e:
        logger.error(f"Error getting top volunteers by events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top volunteers by events"
        )
