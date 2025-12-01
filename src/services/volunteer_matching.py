from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass
from logging import Logger

from src.domain.volunteering import (
    Opportunity, OpportunityId, MatchRequest, MatchRequestId, 
    Match, MatchId, MatchStatus
)
from src.domain.events import EventId
from src.domain.users import UserId
from src.domain.profiles import Profile
from src.domain.repositories import OpportunityRepository, MatchRepository, MatchRequestRepository


@dataclass
class MatchScore:
    """Represents a match score with breakdown."""
    total_score: float
    skill_match_score: float
    availability_score: float
    preference_score: float
    distance_score: float


class VolunteerMatchingService:
    """Service for matching volunteers to events based on their profiles and event requirements."""
    
    def __init__(self, logger: Logger, opportunity_repository: OpportunityRepository, 
                 match_repository: MatchRepository, match_request_repository: MatchRequestRepository) -> None:
        self._logger = logger
        self._opportunity_repository = opportunity_repository
        self._match_repository = match_repository
        self._match_request_repository = match_request_repository
    
    def create_opportunity(
        self,
        event_id: EventId,
        title: str,
        description: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        min_hours: Optional[float] = None,
        max_slots: Optional[int] = None
    ) -> Opportunity:
        """Create a volunteer opportunity for an event."""
        # Validation
        if not title or len(title.strip()) == 0:
            raise ValueError("Opportunity title is required")
        if len(title) > 100:
            raise ValueError("Opportunity title must be 100 characters or less")
        
        if description and len(description) > 500:
            raise ValueError("Opportunity description must be 500 characters or less")
        
        if min_hours is not None and min_hours <= 0:
            raise ValueError("Minimum hours must be greater than 0")
        
        if max_slots is not None and max_slots <= 0:
            raise ValueError("Maximum slots must be greater than 0")
        
        # Create opportunity
        opportunity_id = OpportunityId.new()
        opportunity = Opportunity(
            id=opportunity_id,
            event_id=event_id,
            title=title.strip(),
            description=description.strip() if description else None,
            required_skills=required_skills or [],
            min_hours=min_hours,
            max_slots=max_slots
        )
        
        self._opportunity_repository.add(opportunity)
        self._logger.info(f"Created opportunity: {title} for event {event_id.value}")
        
        return opportunity
    
    def get_opportunity(self, opportunity_id: OpportunityId) -> Optional[Opportunity]:
        """Get an opportunity by ID."""
        return self._opportunity_repository.get(opportunity_id)
    
    def get_opportunities_by_event(self, event_id: EventId) -> List[Opportunity]:
        """Get all opportunities for a specific event."""
        return self._opportunity_repository.list_for_event(event_id)
    
    def get_all_opportunities(self) -> List[Opportunity]:
        """Retrieve all opportunities. Note: This may need pagination for large datasets."""
        return self._opportunity_repository.list_all()
    
    def create_match_request(
        self,
        user_id: UserId,
        opportunity_id: OpportunityId
    ) -> MatchRequest:
        """Create a match request for a volunteer to apply for an opportunity."""
        # Validate opportunity exists
        opportunity = self.get_opportunity(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity does not exist")
        
        # Check if user already has a pending/accepted request for this opportunity
        existing_request = self._find_user_request_for_opportunity(user_id, opportunity_id)
        if existing_request and existing_request.status in [MatchStatus.PENDING, MatchStatus.ACCEPTED]:
            raise ValueError("User already has an active request for this opportunity")
        
        # Create match request
        request_id = MatchRequestId.new()
        match_request = MatchRequest(
            id=request_id,
            user_id=user_id,
            opportunity_id=opportunity_id,
            requested_at=datetime.now(),
            status=MatchStatus.PENDING
        )
        
        self._match_request_repository.add(match_request)
        self._logger.info(f"Created match request for user {user_id.value} to opportunity {opportunity_id.value}")
        
        return match_request
    
    def calculate_match_score(
        self,
        profile: Profile,
        opportunity: Opportunity
    ) -> MatchScore:
        """Calculate how well a volunteer profile matches an opportunity."""
        # Skill matching (40% of total score)
        skill_score = self._calculate_skill_match_score(profile.skills, opportunity.required_skills)
        
        # Availability scoring (30% of total score) - simplified for demo
        availability_score = 0.8 if profile.availability else 0.3
        
        # Preference scoring (20% of total score) - based on tags
        preference_score = self._calculate_preference_score(profile.tags, opportunity)
        
        # Distance scoring (10% of total score) - simplified for demo
        distance_score = 0.7  # Would calculate based on location in real implementation
        
        # Calculate weighted total
        total_score = (
            skill_score * 0.4 +
            availability_score * 0.3 +
            preference_score * 0.2 +
            distance_score * 0.1
        )
        
        return MatchScore(
            total_score=total_score,
            skill_match_score=skill_score,
            availability_score=availability_score,
            preference_score=preference_score,
            distance_score=distance_score
        )
    
    def find_matching_volunteers(
        self,
        opportunity_id: OpportunityId,
        profiles: List[Profile],
        min_score: float = 0.5
    ) -> List[Tuple[Profile, MatchScore]]:
        """Find volunteers that match an opportunity above the minimum score threshold."""
        opportunity = self.get_opportunity(opportunity_id)
        if not opportunity:
            return []
        
        matches = []
        
        for profile in profiles:
            # Skip if user already has an active request/match for this opportunity
            existing_request = self._find_user_request_for_opportunity(profile.user_id, opportunity_id)
            if existing_request and existing_request.status in [MatchStatus.PENDING, MatchStatus.ACCEPTED]:
                continue
            
            score = self.calculate_match_score(profile, opportunity)
            if score.total_score >= min_score:
                matches.append((profile, score))
        
        # Sort by total score (descending)
        matches.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return matches
    
    def find_matching_opportunities(
        self,
        user_id: UserId,
        profile: Profile,
        min_score: float = 0.5
    ) -> List[Tuple[Opportunity, MatchScore]]:
        """Find opportunities that match a volunteer's profile."""
        matches = []
        
        # Get all opportunities and calculate scores
        opportunities = self._opportunity_repository.list_all()
        
        for opportunity in opportunities:
            # Skip if user already has an active request/match for this opportunity
            existing_request = self._find_user_request_for_opportunity(user_id, opportunity.id)
            if existing_request and existing_request.status in [MatchStatus.PENDING, MatchStatus.ACCEPTED]:
                continue
            
            score = self.calculate_match_score(profile, opportunity)
            if score.total_score >= min_score:
                matches.append((opportunity, score))
        
        # Sort by total score (descending)
        matches.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return matches
    
    def approve_match_request(self, request_id: MatchRequestId) -> Optional[Match]:
        """Approve a match request and create a match."""
        request = self._match_request_repository.get(request_id)
        if not request:
            return None
        
        if request.status != MatchStatus.PENDING:
            raise ValueError("Can only approve pending match requests")
        
        # Check if opportunity still has slots available
        opportunity = self.get_opportunity(request.opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity no longer exists")
        
        if opportunity.max_slots:
            current_matches = self._count_matches_for_opportunity(request.opportunity_id)
            if current_matches >= opportunity.max_slots:
                raise ValueError("Opportunity is at maximum capacity")
        
        # Update request status
        request.status = MatchStatus.ACCEPTED
        self._match_request_repository.save(request)
        
        # Create match
        match_id = MatchId.new()
        match = Match(
            id=match_id,
            user_id=request.user_id,
            opportunity_id=request.opportunity_id,
            created_at=datetime.now(),
            status=MatchStatus.ACCEPTED,
            score=request.score
        )
        
        self._match_repository.add(match)
        self._logger.info(f"Approved match request {request_id.value} - created match {match_id.value}")
        
        return match
    
    def reject_match_request(self, request_id: MatchRequestId, reason: Optional[str] = None) -> bool:
        """Reject a match request."""
        request = self._match_request_repository.get(request_id)
        if not request:
            return False
        
        if request.status != MatchStatus.PENDING:
            raise ValueError("Can only reject pending match requests")
        
        request.status = MatchStatus.REJECTED
        self._match_request_repository.save(request)
        self._logger.info(f"Rejected match request {request_id.value}")
        
        return True
    
    def get_match_requests_by_opportunity(self, opportunity_id: OpportunityId) -> List[MatchRequest]:
        """Get all match requests for an opportunity."""
        return self._match_request_repository.list_pending_for_opportunity(opportunity_id)
    
    def get_match_requests_by_user(self, user_id: UserId) -> List[MatchRequest]:
        """Get all match requests by a user."""
        return self._match_request_repository.list_for_user(user_id)
    
    def get_matches_by_user(self, user_id: UserId) -> List[Match]:
        """Get all matches for a user."""
        return self._match_repository.list_for_user(user_id)
    
    def get_matches_by_opportunity(self, opportunity_id: OpportunityId) -> List[Match]:
        """Get all matches for an opportunity."""
        return self._match_repository.list_for_opportunity(opportunity_id)
    
    def cancel_match(self, match_id: MatchId) -> bool:
        """Cancel an existing match."""
        # Note: Repository doesn't support delete, marking as not implemented
        self._logger.warning("cancel_match not fully implemented - repository doesn't support delete")
        return False
    
    def expire_old_requests(self, days_old: int = 30) -> int:
        """Expire match requests older than specified days."""
        # Note: Would need repository support to query by date
        self._logger.warning("expire_old_requests not implemented - requires repository query support")
        return 0
    
    def _calculate_skill_match_score(self, profile_skills: List[str], required_skills: List[str]) -> float:
        """Calculate skill match score between 0.0 and 1.0."""
        if not required_skills:
            return 1.0
        
        if not profile_skills:
            return 0.0
        
        profile_skill_set = set(skill.lower() for skill in profile_skills)
        required_skill_set = set(skill.lower() for skill in required_skills)
        
        matching_skills = profile_skill_set.intersection(required_skill_set)
        return len(matching_skills) / len(required_skill_set)
    
    def _calculate_preference_score(self, profile_tags: List[str], opportunity: Opportunity) -> float:
        """Calculate preference score based on tags and opportunity characteristics."""
        # This is a simplified implementation
        # In reality, you'd have more sophisticated preference matching
        
        if not profile_tags:
            return 0.5  # Neutral score
        
        # Look for relevant tags
        score = 0.5
        tag_set = set(tag.lower() for tag in profile_tags)
        
        # Boost score for relevant tags
        if "experience" in tag_set:
            score += 0.2
        if "leadership" in tag_set and "lead" in opportunity.title.lower():
            score += 0.2
        if "outdoors" in tag_set and any(word in opportunity.title.lower() for word in ["park", "cleanup", "outdoor"]):
            score += 0.3
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _find_user_request_for_opportunity(self, user_id: UserId, opportunity_id: OpportunityId) -> Optional[MatchRequest]:
        """Find a user's match request for a specific opportunity."""
        return self._match_request_repository.find_by_user_and_opportunity(user_id, opportunity_id)
    
    def _count_matches_for_opportunity(self, opportunity_id: OpportunityId) -> int:
        """Count the number of accepted matches for an opportunity."""
        matches = self._match_repository.list_for_opportunity(opportunity_id)
        return len([m for m in matches if m.status == MatchStatus.ACCEPTED])
