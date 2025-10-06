from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
from uuid import UUID


class LocationSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Location name")
    address: Optional[str] = Field(None, max_length=500, description="Address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")


class EventCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Event title")
    description: str = Field(..., min_length=1, max_length=500, description="Event description")
    location: LocationSchema = Field(..., description="Event location")
    required_skills: List[str] = Field(..., description="Required skills")
    starts_at: datetime = Field(..., description="Event start time")
    ends_at: Optional[datetime] = Field(None, description="Event end time")
    capacity: Optional[int] = Field(None, gt=0, description="Event capacity")
    
    @validator('required_skills')
    def validate_skills(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one required skill must be specified')
        return v
    
    @validator('ends_at')
    def ends_at_after_starts_at(cls, v, values):
        if v and 'starts_at' in values and v <= values['starts_at']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('starts_at')
    def starts_at_in_future(cls, v):
        if v <= datetime.now():
            raise ValueError('Start time must be in the future')
        return v


class EventUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="Event title")
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="Event description")
    location: Optional[LocationSchema] = Field(None, description="Event location")
    required_skills: Optional[List[str]] = Field(None, description="Required skills")
    starts_at: Optional[datetime] = Field(None, description="Event start time")
    ends_at: Optional[datetime] = Field(None, description="Event end time")
    capacity: Optional[int] = Field(None, gt=0, description="Event capacity")
    
    @validator('required_skills')
    def validate_skills(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('At least one required skill must be specified')
        return v


class EventResponseSchema(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    location: Optional[LocationSchema]
    required_skills: List[str]
    starts_at: datetime
    ends_at: Optional[datetime]
    capacity: Optional[int]
    status: str
    
    class Config:
        from_attributes = True


class EventListResponseSchema(BaseModel):
    events: List[EventResponseSchema]
    total: int


class EventSearchSchema(BaseModel):
    skills: Optional[List[str]] = Field(None, description="Skills to search for")
    city: Optional[str] = Field(None, description="City to search in")
    state: Optional[str] = Field(None, description="State to search in")
    status: Optional[str] = Field(None, description="Event status filter")