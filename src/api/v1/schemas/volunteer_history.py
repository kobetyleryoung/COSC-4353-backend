from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
from uuid import UUID


class HistoryEntryCreateSchema(BaseModel):
    user_id: str = Field(..., description="User ID (auth0 sub)")
    event_id: str = Field(..., description="Event ID (UUID string)")
    role: str = Field(..., min_length=1, max_length=100, description="Volunteer role")
    hours: float = Field(..., gt=0, le=24, description="Hours volunteered")
    date: datetime = Field(..., description="Date of volunteer work")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @validator('date')
    def date_not_future(cls, v):
        if v > datetime.now():
            raise ValueError('Date cannot be in the future')
        return v


class HistoryEntryUpdateSchema(BaseModel):
    role: Optional[str] = Field(None, min_length=1, max_length=100, description="Volunteer role")
    hours: Optional[float] = Field(None, gt=0, le=24, description="Hours volunteered")
    date: Optional[datetime] = Field(None, description="Date of volunteer work")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @validator('date')
    def date_not_future(cls, v):
        if v and v > datetime.now():
            raise ValueError('Date cannot be in the future')
        return v


class HistoryEntryResponseSchema(BaseModel):
    id: UUID
    user_id: UUID
    event_id: UUID
    role: str
    hours: float
    date: datetime
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class HistoryListResponseSchema(BaseModel):
    entries: List[HistoryEntryResponseSchema]
    total: int


class UserStatsResponseSchema(BaseModel):
    total_hours: float
    total_events: int
    unique_roles: int
    first_volunteer_date: Optional[datetime]
    last_volunteer_date: Optional[datetime]
    average_hours_per_event: float
    most_common_role: Optional[str]


class TopVolunteerResponseSchema(BaseModel):
    user_id: UUID
    value: float  # hours or event count
    

class MonthlyHoursResponseSchema(BaseModel):
    month: int
    hours: float


class YearlyStatsResponseSchema(BaseModel):
    year: int
    monthly_hours: List[MonthlyHoursResponseSchema]
    total_hours: float