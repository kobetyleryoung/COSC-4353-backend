from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID

from src.services.volunteer_matching import VolunteerMatchingService
from src.services.profile_management import ProfileManagementService
from src.domain.users import UserId
from src.domain.volunteering import OpportunityId, MatchRequestId, MatchId
from src.domain.events import EventId
from src.config.database_settings import get_uow
from src.repositories.unit_of_work import UnitOfWorkManager
from ..schemas.volunteer_matching import (
    OpportunityCreateSchema, OpportunityResponseSchema,
    MatchRequestCreateSchema, MatchRequestResponseSchema,
    MatchResponseSchema, MatchScoreResponseSchema,
    VolunteerMatchSchema, OpportunityMatchSchema,
    MatchingVolunteersResponseSchema, MatchingOpportunitiesResponseSchema
)
from src.config.logging_config import logger

router = APIRouter(prefix="/volunteer-matching", tags=["volunteer-matching"])

#region helpers

def _get_matching_service(uow_manager: UnitOfWorkManager = Depends(get_uow)) -> VolunteerMatchingService:
    return VolunteerMatchingService(uow_manager, logger)

def _get_profile_service(uow_manager: UnitOfWorkManager = Depends(get_uow)) -> ProfileManagementService:
    return ProfileManagementService(uow_manager, logger)


def _convert_opportunity_to_response(opportunity) -> OpportunityResponseSchema:
    """Convert domain Opportunity to OpportunityResponseSchema."""
    return OpportunityResponseSchema(
        id=opportunity.id.value,
        event_id=opportunity.event_id.value,
        title=opportunity.title,
        description=opportunity.description,
        required_skills=opportunity.required_skills,
        min_hours=opportunity.min_hours,
        max_slots=opportunity.max_slots
    )


def _convert_match_request_to_response(request) -> MatchRequestResponseSchema:
    """Convert domain MatchRequest to MatchRequestResponseSchema."""
    return MatchRequestResponseSchema(
        id=request.id.value,
        user_id=request.user_id.value,
        opportunity_id=request.opportunity_id.value,
        requested_at=request.requested_at,
        status=request.status.name,
        score=request.score
    )


def _convert_match_to_response(match) -> MatchResponseSchema:
    """Convert domain Match to MatchResponseSchema."""
    return MatchResponseSchema(
        id=match.id.value,
        user_id=match.user_id.value,
        opportunity_id=match.opportunity_id.value,
        created_at=match.created_at,
        status=match.status.name,
        score=match.score
    )


def _convert_match_score_to_response(score) -> MatchScoreResponseSchema:
    """Convert MatchScore to MatchScoreResponseSchema."""
    return MatchScoreResponseSchema(
        total_score=score.total_score,
        skill_match_score=score.skill_match_score,
        availability_score=score.availability_score,
        preference_score=score.preference_score,
        distance_score=score.distance_score
    )

#endregion

@router.get("/opportunities", response_model=List[OpportunityResponseSchema])
async def get_all_opportunities(
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Get all volunteer opportunities."""
    try:
        opportunities = matching_service.get_all_opportunities()
        return [_convert_opportunity_to_response(opp) for opp in opportunities]
    except Exception as e:
        logger.error(f"Error getting all opportunities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve opportunities"
        )


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponseSchema)
async def get_opportunity_by_id(
    opportunity_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Get a specific opportunity by ID."""
    try:
        opportunity = matching_service.get_opportunity_by_id(OpportunityId(opportunity_id))
        if not opportunity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opportunity not found"
            )
        
        return _convert_opportunity_to_response(opportunity)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opportunity {opportunity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve opportunity"
        )


@router.get("/opportunities/by-event/{event_id}", response_model=List[OpportunityResponseSchema])
async def get_opportunities_by_event(
    event_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Get all opportunities for a specific event."""
    try:
        opportunities = matching_service.get_opportunities_by_event(EventId(event_id))
        return [_convert_opportunity_to_response(opp) for opp in opportunities]
    except Exception as e:
        logger.error(f"Error getting opportunities for event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve opportunities for event"
        )


@router.post("/opportunities", response_model=OpportunityResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    opportunity_data: OpportunityCreateSchema,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Create a new volunteer opportunity."""
    try:
        opportunity = matching_service.create_opportunity(
            event_id=EventId(opportunity_data.event_id),
            title=opportunity_data.title,
            description=opportunity_data.description,
            required_skills=opportunity_data.required_skills,
            min_hours=opportunity_data.min_hours,
            max_slots=opportunity_data.max_slots
        )
        
        return _convert_opportunity_to_response(opportunity)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error creating opportunity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create opportunity"
        )


@router.post("/match-requests", response_model=MatchRequestResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_match_request(
    request_data: MatchRequestCreateSchema,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Create a match request for a volunteer to apply for an opportunity."""
    try:
        # In real app, get user_id from authenticated user
        user_id = UserId.new()
        
        match_request = matching_service.create_match_request(
            user_id=user_id,
            opportunity_id=OpportunityId(request_data.opportunity_id)
        )
        
        return _convert_match_request_to_response(match_request)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error creating match request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create match request"
        )


@router.get("/match-requests/by-opportunity/{opportunity_id}", response_model=List[MatchRequestResponseSchema])
async def get_match_requests_by_opportunity(
    opportunity_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Get all match requests for an opportunity."""
    try:
        requests = matching_service.get_match_requests_by_opportunity(OpportunityId(opportunity_id))
        return [_convert_match_request_to_response(req) for req in requests]
    except Exception as e:
        logger.error(f"Error getting match requests for opportunity {opportunity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match requests"
        )


@router.get("/match-requests/by-user/{user_id}", response_model=List[MatchRequestResponseSchema])
async def get_match_requests_by_user(
    user_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Get all match requests by a user."""
    try:
        requests = matching_service.get_match_requests_by_user(UserId(user_id))
        return [_convert_match_request_to_response(req) for req in requests]
    except Exception as e:
        logger.error(f"Error getting match requests for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match requests"
        )


@router.post("/match-requests/{request_id}/approve", response_model=MatchResponseSchema)
async def approve_match_request(
    request_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Approve a match request and create a match."""
    try:
        match = matching_service.approve_match_request(MatchRequestId(request_id))
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match request not found"
            )
        
        return _convert_match_to_response(match)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error approving match request {request_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve match request"
        )


@router.post("/match-requests/{request_id}/reject")
async def reject_match_request(
    request_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Reject a match request."""
    try:
        success = matching_service.reject_match_request(MatchRequestId(request_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match request not found"
            )
        
        return {"message": "Match request rejected successfully"}
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error rejecting match request {request_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject match request"
        )


@router.get("/matches/by-user/{user_id}", response_model=List[MatchResponseSchema])
async def get_matches_by_user(
    user_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Get all matches for a user."""
    try:
        matches = matching_service.get_matches_by_user(UserId(user_id))
        return [_convert_match_to_response(match) for match in matches]
    except Exception as e:
        logger.error(f"Error getting matches for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve matches"
        )


@router.get("/matches/by-opportunity/{opportunity_id}", response_model=List[MatchResponseSchema])
async def get_matches_by_opportunity(
    opportunity_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Get all matches for an opportunity."""
    try:
        matches = matching_service.get_matches_by_opportunity(OpportunityId(opportunity_id))
        return [_convert_match_to_response(match) for match in matches]
    except Exception as e:
        logger.error(f"Error getting matches for opportunity {opportunity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve matches"
        )


@router.delete("/matches/{match_id}")
async def cancel_match(
    match_id: UUID,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Cancel an existing match."""
    try:
        success = matching_service.cancel_match(MatchId(match_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )
        
        return {"message": "Match cancelled successfully"}
    except Exception as e:
        logger.error(f"Error cancelling match {match_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel match"
        )


@router.get("/find-volunteers/{opportunity_id}", response_model=MatchingVolunteersResponseSchema)
async def find_matching_volunteers(
    opportunity_id: UUID,
    min_score: float = 0.5,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service),
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Find volunteers that match an opportunity."""
    try:
        profiles = profile_service.get_all_profiles()
        matches = matching_service.find_matching_volunteers(
            opportunity_id=OpportunityId(opportunity_id),
            profiles=profiles,
            min_score=min_score
        )
        
        volunteer_matches = []
        for profile, score in matches:
            # Convert profile to dict (simplified for demo)
            profile_dict = {
                "user_id": str(profile.user_id.value),
                "display_name": profile.display_name,
                "skills": profile.skills,
                "tags": profile.tags
            }
            
            volunteer_match = VolunteerMatchSchema(
                profile=profile_dict,
                score=_convert_match_score_to_response(score)
            )
            volunteer_matches.append(volunteer_match)
        
        return MatchingVolunteersResponseSchema(
            matches=volunteer_matches,
            total=len(volunteer_matches)
        )
    except Exception as e:
        logger.error(f"Error finding matching volunteers for opportunity {opportunity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find matching volunteers"
        )


@router.get("/find-opportunities/{user_id}", response_model=MatchingOpportunitiesResponseSchema)
async def find_matching_opportunities(
    user_id: UUID,
    min_score: float = 0.5,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service),
    profile_service: ProfileManagementService = Depends(_get_profile_service)
):
    """Find opportunities that match a volunteer profile."""
    try:
        profile = profile_service.get_profile_by_user_id(UserId(user_id))
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        matches = matching_service.find_matching_opportunities(
            user_id=UserId(user_id),
            profile=profile,
            min_score=min_score
        )
        
        opportunity_matches = []
        for opportunity, score in matches:
            opportunity_match = OpportunityMatchSchema(
                opportunity=_convert_opportunity_to_response(opportunity),
                score=_convert_match_score_to_response(score)
            )
            opportunity_matches.append(opportunity_match)
        
        return MatchingOpportunitiesResponseSchema(
            matches=opportunity_matches,
            total=len(opportunity_matches)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding matching opportunities for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find matching opportunities"
        )


@router.post("/expire-old-requests")
async def expire_old_requests(
    days_old: int = 30,
    matching_service: VolunteerMatchingService = Depends(_get_matching_service)
):
    """Expire old match requests."""
    try:
        expired_count = matching_service.expire_old_requests(days_old)
        return {"message": f"Expired {expired_count} old match requests"}
    except Exception as e:
        logger.error(f"Error expiring old requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to expire old requests"
        )
