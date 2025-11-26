from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class HistoryEntryCreateSchema(BaseModel):
    event_id: str = Field(..., description="Event ID (UUID string)")
    role: str = Field(..., min_length=1, max_length=100, description="Volunteer role")
    hours: float = Field(..., gt=0, le=24, description="Hours volunteered")
    date: str = Field(..., description="Date of volunteer work (ISO 8601 format)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class HistoryEntryUpdateSchema(BaseModel):
    role: Optional[str] = Field(None, min_length=1, max_length=100, description="Volunteer role")
    hours: Optional[float] = Field(None, gt=0, le=24, description="Hours volunteered")
    date: Optional[str] = Field(None, description="Date of volunteer work (ISO 8601 format)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class HistoryEntryResponseSchema(BaseModel):
    id: str
    user_id: str
    event_id: str
    role: str
    hours: float
    date: str
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
    first_volunteer_date: Optional[str]
    last_volunteer_date: Optional[str]
    average_hours_per_event: float
    most_common_role: Optional[str]


class MonthlyHoursResponseSchema(BaseModel):
    month: int
    hours: float


class TopVolunteerResponseSchema(BaseModel):
    user_id: str
    display_name: Optional[str]
    total_hours: float
    total_events: int


class YearlyStatsResponseSchema(BaseModel):
    year: int
    monthly_hours: List[MonthlyHoursResponseSchema]
    total_hours: float