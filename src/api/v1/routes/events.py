from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from src.services.event_management import EventManagementService
from src.domain.events import Event, EventId, Location
from src.domain.users import UserId
from src.repositories.database import get_uow
from src.repositories.unit_of_work import UnitOfWorkManager
from src.api.dependencies import get_or_create_user
from ..schemas.events import (
    EventCreateSchema, EventUpdateSchema, EventResponseSchema,
    EventListResponseSchema, LocationSchema, EventSearchSchema
)
from src.repositories.unit_of_work import UnitOfWorkManager
from src.config.logging_config import logger

router = APIRouter(prefix="/events", tags=["events"])

#region helpers

def _get_event_service(uow=Depends(get_uow)) -> EventManagementService:
        return EventManagementService(uow.session, logger)
    
def _convert_location_to_schema(location) -> Optional[LocationSchema]:
    """Convert Location domain model to LocationSchema"""
    if location is None:
        return None
    return LocationSchema(
        name=location.name,
        address=location.address,
        city=location.city,
        state=location.state,
        postal_code=location.postal_code
    )

def _convert_event_to_response(event: Event) -> EventResponseSchema:
    """Convert Event domain model to EventResponseSchema"""
    return EventResponseSchema(
        id=event.id.value,
        title=event.title,
        description=event.description,
        location=_convert_location_to_schema(event.location),
        required_skills=event.required_skills,
        starts_at=event.starts_at.isoformat(),
        ends_at=event.ends_at.isoformat() if event.ends_at else None,
        capacity=event.capacity,
        status=event.status.name
    )

def _convert_events_list_to_response_schema(events: List[Event], total: int) -> EventListResponseSchema:
    """Convert list of Events to EventListResponseSchema"""
    return EventListResponseSchema(
        events=[_convert_event_to_response(event) for event in events],
        total=total
    )
    
def _convert_location_schema_to_domain(location_schema: LocationSchema) -> Location:
    """Convert LocationSchema to domain Location."""
    return Location(
        name=location_schema.name,
        address=location_schema.address,
        city=location_schema.city,
        state=location_schema.state,
        postal_code=location_schema.postal_code
    )

#endregion

@router.get("/", response_model=EventListResponseSchema)
async def get_all_events(
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Get all events."""
    try:
        events = event_service.get_all_events()
        return _convert_events_list_to_response_schema(events, len(events))
    except Exception as e:
        logger.error(f"Error getting all events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events"
        )


@router.get("/published", response_model=EventListResponseSchema)
async def get_published_events(
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Get all published events."""
    try:
        events = event_service.get_published_events()
        return _convert_events_list_to_response_schema(events, len(events))
    except Exception as e:
        logger.error(f"Error getting published events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve published events"
        )


@router.get("/upcoming", response_model=EventListResponseSchema)
async def get_upcoming_events(
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Get upcoming published events."""
    try:
        events = event_service.get_upcoming_events()
        return _convert_events_list_to_response_schema(events, len(events))
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upcoming events"
        )


@router.get("/{event_id}", response_model=EventResponseSchema)
async def get_event_by_id(
    event_id: UUID,
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Get a specific event by ID."""
    try:
        event = event_service.get_event_by_id(EventId(event_id))
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return _convert_event_to_response(event)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event"
        )


@router.post("/", response_model=EventResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreateSchema,
    event_service: EventManagementService = Depends(_get_event_service),
    uow=Depends(get_uow)
):
    """Create a new event. Frontend sends userId in request body."""
    try:
        # Get or create user based on userId from frontend
        user = await get_or_create_user(event_data.user_id, uow)
        
        # Convert schema to domain objects
        location = _convert_location_schema_to_domain(event_data.location)
        
        event = event_service.create_event(
            title=event_data.title,
            description=event_data.description,
            location=location,
            required_skills=event_data.required_skills,
            starts_at=event_data.starts_at,
            ends_at=event_data.ends_at,
            capacity=event_data.capacity
        )
        
        # Automatically create a default volunteer opportunity for this event
        from src.services.volunteer_matching import VolunteerMatchingService
        matching_service = VolunteerMatchingService(logger, uow.opportunities, uow.matches, uow.match_requests)
        matching_service.create_opportunity(
            event_id=event.id,
            title=f"Volunteer for {event_data.title}",
            description=event_data.description,
            required_skills=event_data.required_skills,
            min_hours=None,
            max_slots=event_data.capacity
        )
        
        return _convert_event_to_response(event)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event"
        )


@router.put("/{event_id}", response_model=EventResponseSchema)
async def update_event(
    event_id: UUID,
    event_data: EventUpdateSchema,
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Update an existing event."""
    try:
        # Convert location if provided
        location = None
        if event_data.location:
            location = _convert_location_schema_to_domain(event_data.location)
        
        # Parse datetime strings if provided
        starts_at = None
        if event_data.starts_at:
            starts_at = datetime.fromisoformat(event_data.starts_at.replace('Z', '+00:00'))
        
        ends_at = None
        if event_data.ends_at:
            ends_at = datetime.fromisoformat(event_data.ends_at.replace('Z', '+00:00'))
        
        event = event_service.update_event(
            event_id=EventId(event_id),
            title=event_data.title,
            description=event_data.description,
            location=location,
            required_skills=event_data.required_skills,
            starts_at=starts_at,
            ends_at=ends_at,
            capacity=event_data.capacity
        )
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return _convert_event_to_response(event)
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error updating event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event"
        )


@router.post("/{event_id}/publish")
async def publish_event(
    event_id: UUID,
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Publish an event."""
    try:
        success = event_service.publish_event(EventId(event_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return {"message": "Event published successfully"}
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error publishing event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish event"
        )


@router.post("/{event_id}/cancel")
async def cancel_event(
    event_id: UUID,
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Cancel an event."""
    try:
        success = event_service.cancel_event(EventId(event_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return {"message": "Event cancelled successfully"}
    except Exception as e:
        logger.error(f"Error cancelling event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel event"
        )


@router.delete("/{event_id}")
async def delete_event(
    event_id: UUID,
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Delete an event."""
    try:
        success = event_service.delete_event(EventId(event_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return {"message": "Event deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event"
        )


@router.post("/search", response_model=EventListResponseSchema)
async def search_events(
    search_params: EventSearchSchema,
    event_service: EventManagementService = Depends(_get_event_service)
):
    """Search events by various criteria."""
    try:
        events = []
        
        if search_params.skills:
            events.extend(event_service.get_events_by_skills(search_params.skills))
        
        if search_params.city and search_params.state:
            location_events = event_service.get_events_by_location(
                search_params.city, search_params.state
            )
            events.extend(location_events)
        
        if not search_params.skills and not (search_params.city and search_params.state):
            events = event_service.get_published_events()
        
        # Remove duplicates while preserving order
        seen = set()
        unique_events = []
        for event in events:
            if event.id.value not in seen:
                seen.add(event.id.value)
                unique_events.append(event)
        
        return _convert_events_list_to_response_schema(unique_events, len(unique_events))
    except Exception as e:
        logger.error(f"Error searching events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search events"
        )