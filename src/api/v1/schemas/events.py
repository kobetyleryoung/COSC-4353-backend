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


class EventWindowSchema(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")


class EventCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Event title")
    description: str = Field(..., min_length=1, max_length=500, description="Event description")
    location: Optional[LocationSchema] = Field(None, description="Event location")
    required_skills: List[str] = Field(..., description="Required skills")
    starts_at: str = Field(..., description="Event start datetime (ISO 8601 format)")
    ends_at: Optional[str] = Field(None, description="Event end datetime (ISO 8601 format)")
    capacity: Optional[int] = Field(None, gt=0, description="Event capacity")
    
    @validator('required_skills')
    def validate_skills(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one required skill must be specified')
        return v


class EventUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="Event title")
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="Event description")
    location: Optional[LocationSchema] = Field(None, description="Event location")
    required_skills: Optional[List[str]] = Field(None, description="Required skills")
    starts_at: Optional[str] = Field(None, description="Event start datetime (ISO 8601 format)")
    ends_at: Optional[str] = Field(None, description="Event end datetime (ISO 8601 format)")
    capacity: Optional[int] = Field(None, gt=0, description="Event capacity")
    
    @validator('required_skills')
    def validate_skills(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('At least one required skill must be specified')
        return v


class EventResponseSchema(BaseModel):
    event_id: UUID
    title: str
    description: str
    location: Optional[LocationSchema]
    required_skills: List[str]
    organizer_id: UUID
    schedule: EventWindowSchema
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True