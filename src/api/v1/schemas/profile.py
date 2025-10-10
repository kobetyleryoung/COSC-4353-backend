from pydantic import BaseModel, Field, validator
from datetime import datetime, time
from typing import List, Optional
from uuid import UUID


class AvailabilityWindowSchema(BaseModel):
    weekday: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    start: time = Field(..., description="Start time")
    end: time = Field(..., description="End time")
    
    @validator('end')
    def end_after_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError('End time must be after start time')
        return v


class ProfileCreateSchema(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    skills: List[str] = Field(default_factory=list, description="User skills")
    tags: List[str] = Field(default_factory=list, description="User tags")
    availability: List[AvailabilityWindowSchema] = Field(default_factory=list, description="Availability windows")


class ProfileUpdateSchema(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Display name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    skills: Optional[List[str]] = Field(None, description="User skills")
    tags: Optional[List[str]] = Field(None, description="User tags")
    availability: Optional[List[AvailabilityWindowSchema]] = Field(None, description="Availability windows")


class ProfileResponseSchema(BaseModel):
    user_id: UUID
    display_name: Optional[str]
    phone: Optional[str]
    skills: List[str]
    tags: List[str]
    availability: List[AvailabilityWindowSchema]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AddSkillSchema(BaseModel):
    skill: str = Field(..., min_length=1, description="Skill to add")


class AddTagSchema(BaseModel):
    tag: str = Field(..., min_length=1, description="Tag to add")


class ProfileStatsSchema(BaseModel):
    total_hours: float
    total_events: int
    unique_roles: int
    first_volunteer_date: Optional[datetime]
    last_volunteer_date: Optional[datetime]
    average_hours_per_event: float
    most_common_role: Optional[str]