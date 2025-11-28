from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import UUID

class UserCreateSchema(BaseModel):
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=100)
    auth0_sub: str = Field(..., description="Auth0 subject identifier")

class UserResponseSchema(BaseModel):
    id: UUID
    email: str
    display_name: str
    auth0_sub: Optional[str]
    
    class Config:
        from_attributes = True

class UserUpdateSchema(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)