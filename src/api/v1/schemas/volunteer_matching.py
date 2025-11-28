from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID


class OpportunityCreateSchema(BaseModel):
    event_id: UUID = Field(..., description="Event ID")
    title: str = Field(..., min_length=1, max_length=100, description="Opportunity title")
    description: Optional[str] = Field(None, max_length=500, description="Opportunity description")
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    min_hours: Optional[float] = Field(None, gt=0, description="Minimum hours")
    max_slots: Optional[int] = Field(None, gt=0, description="Maximum slots")


class OpportunityResponseSchema(BaseModel):
    id: UUID
    event_id: UUID
    title: str
    description: Optional[str]
    required_skills: List[str]
    min_hours: Optional[float]
    max_slots: Optional[int]
    
    class Config:
        from_attributes = True


class MatchRequestCreateSchema(BaseModel):
    opportunity_id: UUID = Field(..., description="Opportunity ID")
    user_id: UUID = Field(..., description="User ID")

class MatchRequestResponseSchema(BaseModel):
    id: UUID
    user_id: UUID
    opportunity_id: UUID
    requested_at: datetime
    status: str
    score: Optional[float]
    
    class Config:
        from_attributes = True


class MatchResponseSchema(BaseModel):
    id: UUID
    user_id: UUID
    opportunity_id: UUID
    created_at: datetime
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
    profile: dict  # Profile data
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