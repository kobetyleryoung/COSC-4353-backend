from __future__ import annotations
from datetime import datetime
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
from src.repositories.unit_of_work import UnitOfWorkManager


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
    
    def __init__(self, uow_manager: UnitOfWorkManager, logger: Logger) -> None:
        self._uow_manager = uow_manager
        self._logger = logger
    
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
        
        with self._uow_manager.get_uow() as uow:
            uow.opportunities.add(opportunity)
            uow.commit()
        
        self._logger.info(f"Created opportunity: {title} (ID: {opportunity_id.value})")
        return opportunity
    
    def get_opportunity_by_id(self, opportunity_id: OpportunityId) -> Optional[Opportunity]:
        """Retrieve an opportunity by its ID."""
        with self._uow_manager.get_uow() as uow:
            return uow.opportunities.get_by_id(opportunity_id)
    
    def get_opportunities_by_event(self, event_id: EventId) -> List[Opportunity]:
        """Get all opportunities for a specific event."""
        with self._uow_manager.get_uow() as uow:
            return uow.opportunities.get_by_event(event_id)
    
    def get_all_opportunities(self) -> List[Opportunity]:
        """Get all opportunities."""
        with self._uow_manager.get_uow() as uow:
            return uow.opportunities.list_all()
    
    def create_match_request(
        self,
        user_id: UserId,
        opportunity_id: OpportunityId
    ) -> MatchRequest:
        """Create a match request (volunteer applies to an opportunity)."""
        with self._uow_manager.get_uow() as uow:
            # Check if opportunity exists
            opportunity = uow.opportunities.get_by_id(opportunity_id)
            if not opportunity:
                raise ValueError("Opportunity not found")
            
            # Check if request already exists
            existing_requests = uow.match_requests.get_by_user(user_id)
            for request in existing_requests:
                if request.opportunity_id == opportunity_id:
                    raise ValueError("Match request already exists for this opportunity")
            
            # Create match request
            request_id = MatchRequestId.new()
            match_request = MatchRequest(
                id=request_id,
                user_id=user_id,
                opportunity_id=opportunity_id,
                requested_at=datetime.now(),
                status=MatchStatus.REQUESTED,
                score=None
            )
            
            uow.match_requests.add(match_request)
            uow.commit()
        
        self._logger.info(f"Created match request for user {user_id.value}, opportunity {opportunity_id.value}")
        return match_request
    
    def get_match_requests_by_user(self, user_id: UserId) -> List[MatchRequest]:
        """Get all match requests for a user."""
        with self._uow_manager.get_uow() as uow:
            return uow.match_requests.get_by_user(user_id)
    
    def get_match_requests_by_opportunity(self, opportunity_id: OpportunityId) -> List[MatchRequest]:
        """Get all match requests for an opportunity."""
        with self._uow_manager.get_uow() as uow:
            return uow.match_requests.get_by_opportunity(opportunity_id)
    
    def approve_match_request(
        self,
        request_id: MatchRequestId,
        score: Optional[float] = None
    ) -> Match:
        """Approve a match request and create a match."""
        with self._uow_manager.get_uow() as uow:
            match_request = uow.match_requests.get_by_id(request_id)
            if not match_request:
                raise ValueError("Match request not found")
            
            if match_request.status != MatchStatus.REQUESTED:
                raise ValueError("Match request is not in REQUESTED status")
            
            # Update match request status
            match_request.status = MatchStatus.CONFIRMED
            match_request.score = score
            uow.match_requests.update(match_request)
            
            # Create match
            match_id = MatchId.new()
            match = Match(
                id=match_id,
                user_id=match_request.user_id,
                opportunity_id=match_request.opportunity_id,
                created_at=datetime.now(),
                status=MatchStatus.CONFIRMED,
                score=score
            )
            
            uow.matches.add(match)
            uow.commit()
        
        self._logger.info(f"Approved match request {request_id.value}")
        return match
    
    def reject_match_request(self, request_id: MatchRequestId) -> bool:
        """Reject a match request."""
        with self._uow_manager.get_uow() as uow:
            match_request = uow.match_requests.get_by_id(request_id)
            if not match_request:
                return False
            
            if match_request.status != MatchStatus.REQUESTED:
                raise ValueError("Match request is not in REQUESTED status")
            
            match_request.status = MatchStatus.REJECTED
            uow.match_requests.update(match_request)
            uow.commit()
        
        self._logger.info(f"Rejected match request {request_id.value}")
        return True
    
    def get_matches_by_user(self, user_id: UserId) -> List[Match]:
        """Get all matches for a user."""
        with self._uow_manager.get_uow() as uow:
            return uow.matches.get_by_user(user_id)
    
    def get_matches_by_opportunity(self, opportunity_id: OpportunityId) -> List[Match]:
        """Get all matches for an opportunity."""
        with self._uow_manager.get_uow() as uow:
            return uow.matches.get_by_opportunity(opportunity_id)
    
    def cancel_match(self, match_id: MatchId) -> bool:
        """Cancel an existing match."""
        with self._uow_manager.get_uow() as uow:
            match = uow.matches.get_by_id(match_id)
            if not match:
                return False
            
            match.status = MatchStatus.CANCELLED
            uow.matches.update(match)
            uow.commit()
        
        self._logger.info(f"Cancelled match {match_id.value}")
        return True
    
    def find_matching_opportunities(
        self,
        user_id: UserId,
        min_score: float = 0.5
    ) -> List[Tuple[Opportunity, MatchScore]]:
        """Find opportunities that match a volunteer's profile."""
        with self._uow_manager.get_uow() as uow:
            profile = uow.profiles.get(user_id)
            if not profile:
                return []
            
            all_opportunities = uow.opportunities.list_all()
        
        matches = []
        for opportunity in all_opportunities:
            score = self._calculate_match_score(profile, opportunity)
            if score.total_score >= min_score:
                matches.append((opportunity, score))
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x[1].total_score, reverse=True)
        return matches
    
    def find_matching_volunteers(
        self,
        opportunity_id: OpportunityId,
        min_score: float = 0.5
    ) -> List[Tuple[Profile, MatchScore]]:
        """Find volunteers that match an opportunity's requirements."""
        with self._uow_manager.get_uow() as uow:
            opportunity = uow.opportunities.get_by_id(opportunity_id)
            if not opportunity:
                return []
            
            all_profiles = uow.profiles.get_all()
        
        matches = []
        for profile in all_profiles:
            score = self._calculate_match_score(profile, opportunity)
            if score.total_score >= min_score:
                matches.append((profile, score))
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x[1].total_score, reverse=True)
        return matches
    
    def _calculate_match_score(self, profile: Profile, opportunity: Opportunity) -> MatchScore:
        """Calculate match score between a profile and an opportunity."""
        # Skill matching (40% weight)
        skill_score = self._calculate_skill_match(profile.skills, opportunity.required_skills)
        
        # Availability matching (30% weight)
        availability_score = self._calculate_availability_match(
            profile.availability,
            opportunity.min_hours or 0
        )
        
        # Preference matching (20% weight) - based on tags
        preference_score = self._calculate_preference_match(profile.tags, opportunity.title)
        
        # Distance matching (10% weight) - placeholder for now
        distance_score = 0.5  # Would calculate based on location in real implementation
        
        # Calculate total score
        total_score = (
            0.4 * skill_score +
            0.3 * availability_score +
            0.2 * preference_score +
            0.1 * distance_score
        )
        
        return MatchScore(
            total_score=total_score,
            skill_match_score=skill_score,
            availability_score=availability_score,
            preference_score=preference_score,
            distance_score=distance_score
        )
    
    def _calculate_skill_match(self, user_skills: List[str], required_skills: List[str]) -> float:
        """Calculate skill match score."""
        if not required_skills:
            return 1.0
        
        user_skills_lower = set(skill.lower() for skill in user_skills)
        required_skills_lower = set(skill.lower() for skill in required_skills)
        
        matched_skills = user_skills_lower.intersection(required_skills_lower)
        return len(matched_skills) / len(required_skills_lower)
    
    def _calculate_availability_match(self, availability_windows, min_hours: float) -> float:
        """Calculate availability match score."""
        if not availability_windows:
            return 0.0
        
        # Simple heuristic: more availability windows = higher score
        # In real implementation, would check actual time availability
        total_available_hours = len(availability_windows) * 4  # Assume 4 hours per window
        
        if total_available_hours >= min_hours:
            return 1.0
        else:
            return total_available_hours / max(min_hours, 1)
    
    def _calculate_preference_match(self, user_tags: List[str], opportunity_title: str) -> float:
        """Calculate preference match score based on tags."""
        if not user_tags:
            return 0.5  # Neutral score if no tags
        
        # Check if any tags appear in opportunity title
        title_lower = opportunity_title.lower()
        matching_tags = sum(1 for tag in user_tags if tag.lower() in title_lower)
        
        if matching_tags > 0:
            return min(1.0, matching_tags * 0.5)
        
        return 0.3  # Base score if no direct matches
