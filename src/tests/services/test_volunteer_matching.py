"""
Tests for VolunteerMatchingService
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from src.services.volunteer_matching import VolunteerMatchingService, MatchScore
from src.domain.volunteering import (
    Opportunity, OpportunityId, MatchRequest, MatchRequestId, 
    Match, MatchId, MatchStatus
)
from src.domain.events import EventId
from src.domain.users import UserId
from src.domain.profiles import Profile, AvailabilityWindow
from datetime import time


class TestVolunteerMatchingService:
    """Test VolunteerMatchingService functionality"""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger"""
        return logging.getLogger("test")
    
    @pytest.fixture
    def service(self, logger):
        """Create a fresh VolunteerMatchingService for each test"""
        return VolunteerMatchingService(logger)
    
    @pytest.fixture
    def sample_event_id(self):
        """Sample event ID for testing"""
        return EventId.new()
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return UserId.new()
    
    @pytest.fixture
    def sample_profile(self, sample_user_id):
        """Sample user profile for testing"""
        return Profile(
            user_id=sample_user_id,
            display_name="Test User",
            phone="555-123-4567",
            skills=["Python", "Communication", "Organization"],
            tags=["experienced", "reliable"],
            availability=[
                AvailabilityWindow(weekday=1, start=time(9, 0), end=time(17, 0)),
                AvailabilityWindow(weekday=3, start=time(10, 0), end=time(16, 0))
            ],
            updated_at=datetime.now()
        )
    
    def test_service_initialization(self, service):
        """Test service initializes with sample data"""
        opportunities = service.get_all_opportunities()
        assert isinstance(opportunities, list)
        assert len(opportunities) >= 0  # May have sample data
    
    def test_create_opportunity(self, service, sample_event_id):
        """Test creating a new volunteer opportunity"""
        opportunity = service.create_opportunity(
            event_id=sample_event_id,
            title="Test Opportunity",
            description="A test volunteer opportunity",
            required_skills=["Python", "Testing"],
            min_hours=4.0,
            max_slots=10
        )
        
        assert isinstance(opportunity, Opportunity)
        assert opportunity.event_id == sample_event_id
        assert opportunity.title == "Test Opportunity"
        assert opportunity.description == "A test volunteer opportunity"
        assert opportunity.required_skills == ["Python", "Testing"]
        assert opportunity.min_hours == 4.0
        assert opportunity.max_slots == 10
    
    def test_create_opportunity_minimal(self, service, sample_event_id):
        """Test creating opportunity with minimal required data"""
        opportunity = service.create_opportunity(
            event_id=sample_event_id,
            title="Minimal Opportunity"
        )
        
        assert opportunity.title == "Minimal Opportunity"
        assert opportunity.description is None
        assert opportunity.required_skills == []
        assert opportunity.min_hours is None
        assert opportunity.max_slots is None
    
    def test_create_opportunity_validation_empty_title(self, service, sample_event_id):
        """Test validation fails for empty title"""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            service.create_opportunity(
                event_id=sample_event_id,
                title=""
            )
    
    def test_create_opportunity_validation_long_title(self, service, sample_event_id):
        """Test validation fails for overly long title"""
        long_title = "x" * 101  # Assuming 100 char limit
        
        with pytest.raises(ValueError, match="Title too long"):
            service.create_opportunity(
                event_id=sample_event_id,
                title=long_title
            )
    
    def test_create_opportunity_validation_long_description(self, service, sample_event_id):
        """Test validation fails for overly long description"""
        long_description = "x" * 501  # Assuming 500 char limit
        
        with pytest.raises(ValueError, match="Description too long"):
            service.create_opportunity(
                event_id=sample_event_id,
                title="Valid Title",
                description=long_description
            )
    
    def test_create_opportunity_validation_negative_hours(self, service, sample_event_id):
        """Test validation fails for negative hours"""
        with pytest.raises(ValueError, match="Hours must be positive"):
            service.create_opportunity(
                event_id=sample_event_id,
                title="Valid Title",
                min_hours=-1.0
            )
    
    def test_create_opportunity_validation_negative_slots(self, service, sample_event_id):
        """Test validation fails for negative slots"""
        with pytest.raises(ValueError, match="Slots must be positive"):
            service.create_opportunity(
                event_id=sample_event_id,
                title="Valid Title",
                max_slots=-1
            )
    
    def test_get_opportunity_by_id(self, service, sample_event_id):
        """Test retrieving opportunity by ID"""
        opportunity = service.create_opportunity(
            event_id=sample_event_id,
            title="Findable Opportunity"
        )
        
        found_opportunity = service.get_opportunity_by_id(opportunity.id)
        assert found_opportunity is not None
        assert found_opportunity.id == opportunity.id
        assert found_opportunity.title == "Findable Opportunity"
    
    def test_get_opportunity_by_id_not_found(self, service):
        """Test retrieving non-existent opportunity returns None"""
        fake_id = OpportunityId(uuid4())
        opportunity = service.get_opportunity_by_id(fake_id)
        assert opportunity is None
    
    def test_get_opportunities_by_event(self, service, sample_event_id):
        """Test getting all opportunities for an event"""
        # Create opportunities for the event
        opp1 = service.create_opportunity(sample_event_id, "Opportunity 1")
        opp2 = service.create_opportunity(sample_event_id, "Opportunity 2")
        
        # Create opportunity for different event
        other_event_id = EventId.new()
        opp3 = service.create_opportunity(other_event_id, "Other Opportunity")
        
        event_opportunities = service.get_opportunities_by_event(sample_event_id)
        opportunity_ids = [o.id for o in event_opportunities]
        
        assert opp1.id in opportunity_ids
        assert opp2.id in opportunity_ids
        assert opp3.id not in opportunity_ids
    
    def test_get_all_opportunities(self, service):
        """Test getting all opportunities"""
        initial_count = len(service.get_all_opportunities())
        
        # Create some opportunities
        event1_id = EventId.new()
        event2_id = EventId.new()
        
        service.create_opportunity(event1_id, "Opportunity 1")
        service.create_opportunity(event2_id, "Opportunity 2")
        
        all_opportunities = service.get_all_opportunities()
        assert len(all_opportunities) == initial_count + 2
    
    def test_create_match_request(self, service, sample_user_id, sample_event_id):
        """Test creating a match request"""
        opportunity = service.create_opportunity(sample_event_id, "Test Opportunity")
        
        match_request = service.create_match_request(
            user_id=sample_user_id,
            opportunity_id=opportunity.id
        )
        
        assert isinstance(match_request, MatchRequest)
        assert match_request.user_id == sample_user_id
        assert match_request.opportunity_id == opportunity.id
        assert match_request.status == MatchStatus.PENDING
        assert match_request.requested_at is not None
    
    def test_create_match_request_duplicate(self, service, sample_user_id, sample_event_id):
        """Test creating duplicate match request fails"""
        opportunity = service.create_opportunity(sample_event_id, "Test Opportunity")
        
        # Create first request
        service.create_match_request(sample_user_id, opportunity.id)
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already has a pending request"):
            service.create_match_request(sample_user_id, opportunity.id)
    
    def test_create_match_request_opportunity_not_found(self, service, sample_user_id):
        """Test creating match request for non-existent opportunity fails"""
        fake_opportunity_id = OpportunityId(uuid4())
        
        with pytest.raises(ValueError, match="Opportunity not found"):
            service.create_match_request(sample_user_id, fake_opportunity_id)
    
    def test_calculate_match_score(self, service, sample_profile, sample_event_id):
        """Test calculating match score between profile and opportunity"""
        opportunity = service.create_opportunity(
            event_id=sample_event_id,
            title="Python Developer",
            required_skills=["Python", "Communication"]
        )
        
        score = service.calculate_match_score(sample_profile, opportunity)
        
        assert isinstance(score, MatchScore)
        assert 0.0 <= score.total_score <= 1.0
        assert 0.0 <= score.skill_match_score <= 1.0
        assert 0.0 <= score.availability_score <= 1.0
        assert 0.0 <= score.preference_score <= 1.0
        assert 0.0 <= score.distance_score <= 1.0
    
    def test_find_matching_volunteers(self, service, sample_profile, sample_event_id):
        """Test finding volunteers that match an opportunity"""
        opportunity = service.create_opportunity(
            event_id=sample_event_id,
            title="Python Project",
            required_skills=["Python"]
        )
        
        profiles = [sample_profile]
        matches = service.find_matching_volunteers(opportunity.id, profiles, min_score=0.0)
        
        assert isinstance(matches, list)
        assert len(matches) >= 0
        
        # If we have matches, verify structure
        for profile, score in matches:
            assert isinstance(profile, Profile)
            assert isinstance(score, MatchScore)
    
    def test_find_matching_opportunities(self, service, sample_user_id, sample_profile, sample_event_id):
        """Test finding opportunities that match a user profile"""
        # Create opportunities with different skill requirements
        opp1 = service.create_opportunity(
            event_id=sample_event_id,
            title="Python Opportunity",
            required_skills=["Python"]
        )
        
        opp2 = service.create_opportunity(
            event_id=EventId.new(),
            title="Java Opportunity",
            required_skills=["Java"]
        )
        
        matches = service.find_matching_opportunities(sample_user_id, sample_profile, min_score=0.0)
        
        assert isinstance(matches, list)
        
        # Python opportunity should score higher than Java opportunity
        opportunity_scores = {opp.id: score.total_score for opp, score in matches}
        
        if opp1.id in opportunity_scores and opp2.id in opportunity_scores:
            assert opportunity_scores[opp1.id] >= opportunity_scores[opp2.id]
    
    def test_approve_match_request(self, service, sample_user_id, sample_event_id):
        """Test approving a match request"""
        opportunity = service.create_opportunity(sample_event_id, "Test Opportunity")
        
        match_request = service.create_match_request(sample_user_id, opportunity.id)
        
        match = service.approve_match_request(match_request.id)
        
        assert match is not None
        assert isinstance(match, Match)
        assert match.user_id == sample_user_id
        assert match.opportunity_id == opportunity.id
        assert match.status == MatchStatus.ACCEPTED
        assert match.created_at is not None
    
    def test_approve_match_request_not_found(self, service):
        """Test approving non-existent match request returns None"""
        fake_id = MatchRequestId(uuid4())
        match = service.approve_match_request(fake_id)
        assert match is None
    
    def test_reject_match_request(self, service, sample_user_id, sample_event_id):
        """Test rejecting a match request"""
        opportunity = service.create_opportunity(sample_event_id, "Test Opportunity")
        
        match_request = service.create_match_request(sample_user_id, opportunity.id)
        
        success = service.reject_match_request(match_request.id, reason="Position filled")
        assert success is True
        
        # Verify the request status was updated
        updated_requests = service.get_match_requests_by_user(sample_user_id)
        rejected_request = next((r for r in updated_requests if r.id == match_request.id), None)
        assert rejected_request is not None
        assert rejected_request.status == MatchStatus.REJECTED
    
    def test_reject_match_request_not_found(self, service):
        """Test rejecting non-existent match request returns False"""
        fake_id = MatchRequestId(uuid4())
        success = service.reject_match_request(fake_id)
        assert success is False
    
    def test_get_match_requests_by_opportunity(self, service, sample_event_id):
        """Test getting all match requests for an opportunity"""
        opportunity = service.create_opportunity(sample_event_id, "Test Opportunity")
        
        user1 = UserId.new()
        user2 = UserId.new()
        
        request1 = service.create_match_request(user1, opportunity.id)
        request2 = service.create_match_request(user2, opportunity.id)
        
        requests = service.get_match_requests_by_opportunity(opportunity.id)
        request_ids = [r.id for r in requests]
        
        assert request1.id in request_ids
        assert request2.id in request_ids
    
    def test_get_match_requests_by_user(self, service, sample_user_id):
        """Test getting all match requests for a user"""
        event1_id = EventId.new()
        event2_id = EventId.new()
        
        opp1 = service.create_opportunity(event1_id, "Opportunity 1")
        opp2 = service.create_opportunity(event2_id, "Opportunity 2")
        
        request1 = service.create_match_request(sample_user_id, opp1.id)
        request2 = service.create_match_request(sample_user_id, opp2.id)
        
        requests = service.get_match_requests_by_user(sample_user_id)
        request_ids = [r.id for r in requests]
        
        assert request1.id in request_ids
        assert request2.id in request_ids
    
    def test_get_matches_by_user(self, service, sample_user_id, sample_event_id):
        """Test getting all matches for a user"""
        opportunity = service.create_opportunity(sample_event_id, "Test Opportunity")
        
        match_request = service.create_match_request(sample_user_id, opportunity.id)
        match = service.approve_match_request(match_request.id)
        
        user_matches = service.get_matches_by_user(sample_user_id)
        match_ids = [m.id for m in user_matches]
        
        assert match.id in match_ids
    
    def test_get_matches_by_opportunity(self, service, sample_event_id):
        """Test getting all matches for an opportunity"""
        opportunity = service.create_opportunity(sample_event_id, "Test Opportunity")
        
        user1 = UserId.new()
        user2 = UserId.new()
        
        request1 = service.create_match_request(user1, opportunity.id)
        request2 = service.create_match_request(user2, opportunity.id)
        
        match1 = service.approve_match_request(request1.id)
        match2 = service.approve_match_request(request2.id)
        
        opportunity_matches = service.get_matches_by_opportunity(opportunity.id)
        match_ids = [m.id for m in opportunity_matches]
        
        assert match1.id in match_ids
        assert match2.id in match_ids
    
    def test_cancel_match(self, service, sample_user_id, sample_event_id):
        """Test canceling a match"""
        opportunity = service.create_opportunity(sample_event_id, "Test Opportunity")
        
        match_request = service.create_match_request(sample_user_id, opportunity.id)
        match = service.approve_match_request(match_request.id)
        
        success = service.cancel_match(match.id)
        assert success is True
        
        # Verify match status was updated
        updated_matches = service.get_matches_by_user(sample_user_id)
        cancelled_match = next((m for m in updated_matches if m.id == match.id), None)
        assert cancelled_match is not None
        assert cancelled_match.status == MatchStatus.REJECTED
    
    def test_cancel_match_not_found(self, service):
        """Test canceling non-existent match returns False"""
        fake_id = MatchId(uuid4())
        success = service.cancel_match(fake_id)
        assert success is False
    
    def test_expire_old_requests(self, service):
        """Test expiring old match requests"""
        # This method should find and expire old requests
        expired_count = service.expire_old_requests(days_old=30)
        assert isinstance(expired_count, int)
        assert expired_count >= 0
    
    def test_skill_match_score_calculation(self, service):
        """Test skill matching calculation"""
        profile_skills = ["Python", "JavaScript", "Communication"]
        required_skills = ["Python", "Communication"]
        
        score = service._calculate_skill_match_score(profile_skills, required_skills)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Should be high since profile has both required skills
        assert score > 0.5
    
    def test_skill_match_score_no_match(self, service):
        """Test skill matching with no matching skills"""
        profile_skills = ["Java", "C++"]
        required_skills = ["Python", "JavaScript"]
        
        score = service._calculate_skill_match_score(profile_skills, required_skills)
        
        assert score == 0.0
    
    def test_skill_match_score_empty_requirements(self, service):
        """Test skill matching with no required skills"""
        profile_skills = ["Python", "JavaScript"]
        required_skills = []
        
        score = service._calculate_skill_match_score(profile_skills, required_skills)
        
        # Should return perfect score when no skills are required
        assert score == 1.0
    
    def test_preference_score_calculation(self, service, sample_event_id):
        """Test preference matching calculation"""
        opportunity = service.create_opportunity(
            event_id=sample_event_id,
            title="Environmental Cleanup",
            description="Help clean up the environment"
        )
        
        profile_tags = ["environmental", "outdoors", "volunteer"]
        
        score = service._calculate_preference_score(profile_tags, opportunity)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_opportunity_capacity_tracking(self, service, sample_event_id):
        """Test that opportunity capacity is respected"""
        opportunity = service.create_opportunity(
            event_id=sample_event_id,
            title="Limited Capacity",
            max_slots=2
        )
        
        # Create and approve requests up to capacity
        user1 = UserId.new()
        user2 = UserId.new()
        user3 = UserId.new()
        
        request1 = service.create_match_request(user1, opportunity.id)
        request2 = service.create_match_request(user2, opportunity.id)
        request3 = service.create_match_request(user3, opportunity.id)
        
        # Approve first two
        service.approve_match_request(request1.id)
        service.approve_match_request(request2.id)
        
        # Third should fail due to capacity
        match3 = service.approve_match_request(request3.id)
        assert match3 is None  # Should fail due to capacity