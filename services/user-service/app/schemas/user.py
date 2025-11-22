"""User and Profile schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileBase(BaseModel):
    """Base profile schema."""
    name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ProfileCreate(ProfileBase):
    """Profile creation schema."""
    pass


class ProfileUpdate(BaseModel):
    """Profile update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ProfileResponse(ProfileBase):
    """Profile response schema."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
