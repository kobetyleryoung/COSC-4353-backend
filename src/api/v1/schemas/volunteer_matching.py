from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID


class OpportunityCreateSchema(BaseModel):
    event_id: UUID = Field(..., description="Event ID")
    title: str = Field(..., min_length=1, max_length=200, description="Opportunity title")
    description: Optional[str] = Field(None, max_length=1000, description="Opportunity description")
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    min_hours: Optional[float] = Field(None, gt=0, description="Minimum hours required")
    max_slots: Optional[int] = Field(None, gt=0, description="Maximum number of volunteer slots")


class OpportunityResponseSchema(BaseModel):
    id: str
    event_id: str
    title: str
    description: Optional[str]
    required_skills: List[str]
    min_hours: Optional[float]
    max_slots: Optional[int]
    
    class Config:
        from_attributes = True


class MatchRequestCreateSchema(BaseModel):
    opportunity_id: str = Field(..., description="Opportunity ID (UUID string)")


class MatchRequestResponseSchema(BaseModel):
    id: str
    user_id: str
    opportunity_id: str
    requested_at: str
    status: str
    score: Optional[float]
    
    class Config:
        from_attributes = True


class MatchResponseSchema(BaseModel):
    id: str
    user_id: str
    opportunity_id: str
    created_at: str
    status: str
    score: Optional[float]
    
    class Config:
        from_attributes = True


class MatchScoreResponseSchema(BaseModel):
    total_score: float
    skill_match_score: float
    availability_score: float
    preference_score: float
    distance_score: float


class VolunteerMatchSchema(BaseModel):
    profile: Dict[str, Any]  # Profile data
    score: MatchScoreResponseSchema
    
    
class OpportunityMatchSchema(BaseModel):
    opportunity: OpportunityResponseSchema
    score: MatchScoreResponseSchema


class MatchingVolunteersResponseSchema(BaseModel):
    matches: List[VolunteerMatchSchema]
    total: int


class MatchingOpportunitiesResponseSchema(BaseModel):
    matches: List[OpportunityMatchSchema]
    total: int