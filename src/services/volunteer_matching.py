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
    
    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        # Hard-coded data storage (no database implementation)
        self._opportunities: dict[str, Opportunity] = {}
        self._match_requests: dict[str, MatchRequest] = {}
        self._matches: dict[str, Match] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self) -> None:
        """Initialize with sample opportunities and matches."""
        # Sample opportunities (would typically come from EventManagementService)
        event1_id = EventId.new()
        opp1_id = OpportunityId.new()
        opportunity1 = Opportunity(
            id=opp1_id,
            event_id=event1_id,
            title="Park Cleanup Volunteer",
            description="General cleanup tasks including trash pickup and landscaping",
            required_skills=["Physical Labor", "Environmental Awareness"],
            min_hours=4.0,
            max_slots=20
        )
        self._opportunities[str(opp1_id.value)] = opportunity1
        
        event2_id = EventId.new()
        opp2_id = OpportunityId.new()
        opportunity2 = Opportunity(
            id=opp2_id,
            event_id=event2_id,
            title="Food Distribution Assistant",
            description="Help organize and distribute food packages to families",
            required_skills=["Customer Service", "Organization"],
            min_hours=3.0,
            max_slots=15
        )
        self._opportunities[str(opp2_id.value)] = opportunity2
        
        event3_id = EventId.new()
        opp3_id = OpportunityId.new()
        opportunity3 = Opportunity(
            id=opp3_id,
            event_id=event3_id,
            title="Senior Companion",
            description="Provide companionship and assist with recreational activities",
            required_skills=["Communication", "Patience"],
            min_hours=2.0,
            max_slots=8
        )
        self._opportunities[str(opp3_id.value)] = opportunity3
        
        self._logger.info(f"Initialized {len(self._opportunities)} sample opportunities")
    
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
        
        self._opportunities[str(opportunity_id.value)] = opportunity
        self._logger.info(f"Created opportunity: {title} for event {event_id.value}")
        
        return opportunity
    
    def get_opportunity_by_id(self, opportunity_id: OpportunityId) -> Optional[Opportunity]:
        """Retrieve an opportunity by its ID."""
        return self._opportunities.get(str(opportunity_id.value))
    
    def get_opportunities_by_event(self, event_id: EventId) -> List[Opportunity]:
        """Get all opportunities for a specific event."""
        return [
            opp for opp in self._opportunities.values()
            if opp.event_id.value == event_id.value
        ]
    
    def get_all_opportunities(self) -> List[Opportunity]:
        """Retrieve all opportunities."""
        return list(self._opportunities.values())
    
    def create_match_request(
        self,
        user_id: UserId,
        opportunity_id: OpportunityId
    ) -> MatchRequest:
        """Create a match request for a volunteer to apply for an opportunity."""
        # Validate opportunity exists
        opportunity = self.get_opportunity_by_id(opportunity_id)
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
        
        self._match_requests[str(request_id.value)] = match_request
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
        opportunity = self.get_opportunity_by_id(opportunity_id)
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
        """Find opportunities that match a volunteer profile above the minimum score threshold."""
        matches = []
        
        for opportunity in self._opportunities.values():
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
        request = self._match_requests.get(str(request_id.value))
        if not request:
            return None
        
        if request.status != MatchStatus.PENDING:
            raise ValueError("Can only approve pending match requests")
        
        # Check if opportunity still has slots available
        opportunity = self.get_opportunity_by_id(request.opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity no longer exists")
        
        if opportunity.max_slots:
            current_matches = self._count_matches_for_opportunity(request.opportunity_id)
            if current_matches >= opportunity.max_slots:
                raise ValueError("Opportunity is at maximum capacity")
        
        # Update request status
        request.status = MatchStatus.ACCEPTED
        
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
        
        self._matches[str(match_id.value)] = match
        self._logger.info(f"Approved match request {request_id.value}, created match {match_id.value}")
        
        return match
    
    def reject_match_request(self, request_id: MatchRequestId, reason: Optional[str] = None) -> bool:
        """Reject a match request."""
        request = self._match_requests.get(str(request_id.value))
        if not request:
            return False
        
        if request.status != MatchStatus.PENDING:
            raise ValueError("Can only reject pending match requests")
        
        request.status = MatchStatus.REJECTED
        self._logger.info(f"Rejected match request {request_id.value}")
        
        return True
    
    def get_match_requests_by_opportunity(self, opportunity_id: OpportunityId) -> List[MatchRequest]:
        """Get all match requests for an opportunity."""
        return [
            request for request in self._match_requests.values()
            if request.opportunity_id.value == opportunity_id.value
        ]
    
    def get_match_requests_by_user(self, user_id: UserId) -> List[MatchRequest]:
        """Get all match requests by a user."""
        return [
            request for request in self._match_requests.values()
            if request.user_id.value == user_id.value
        ]
    
    def get_matches_by_user(self, user_id: UserId) -> List[Match]:
        """Get all matches for a user."""
        return [
            match for match in self._matches.values()
            if match.user_id.value == user_id.value
        ]
    
    def get_matches_by_opportunity(self, opportunity_id: OpportunityId) -> List[Match]:
        """Get all matches for an opportunity."""
        return [
            match for match in self._matches.values()
            if match.opportunity_id.value == opportunity_id.value
        ]
    
    def cancel_match(self, match_id: MatchId) -> bool:
        """Cancel an existing match."""
        match = self._matches.get(str(match_id.value))
        if not match:
            return False
        
        # Remove the match
        del self._matches[str(match_id.value)]
        
        # Find and update corresponding match request
        for request in self._match_requests.values():
            if (request.user_id.value == match.user_id.value and
                request.opportunity_id.value == match.opportunity_id.value and
                request.status == MatchStatus.ACCEPTED):
                request.status = MatchStatus.REJECTED
                break
        
        self._logger.info(f"Cancelled match {match_id.value}")
        return True
    
    def expire_old_requests(self, days_old: int = 30) -> int:
        """Expire match requests older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        expired_count = 0
        
        for request in self._match_requests.values():
            if (request.status == MatchStatus.PENDING and
                request.requested_at < cutoff_date):
                request.status = MatchStatus.EXPIRED
                expired_count += 1
        
        self._logger.info(f"Expired {expired_count} old match requests")
        return expired_count
    
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
        """Find a user's request for a specific opportunity."""
        for request in self._match_requests.values():
            if (request.user_id.value == user_id.value and
                request.opportunity_id.value == opportunity_id.value):
                return request
        return None
    
    def _count_matches_for_opportunity(self, opportunity_id: OpportunityId) -> int:
        """Count the number of active matches for an opportunity."""
        return len([
            match for match in self._matches.values()
            if match.opportunity_id.value == opportunity_id.value and
            match.status == MatchStatus.ACCEPTED
        ])
