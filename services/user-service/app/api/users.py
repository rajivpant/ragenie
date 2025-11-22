"""User and Profile API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

# Import shared models
import sys
sys.path.append('/app/../../shared')
from models.user import User
from models.profile import Profile

from app.db.database import get_db
from app.schemas.user import UserResponse, ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter()


# Dependency to get current user (simplified - would integrate with auth service)
async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from token (placeholder)."""
    # TODO: Integrate with auth service to validate JWT and get user
    # For now, return first user (development only)
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.get("/profiles", response_model=List[ProfileResponse])
async def list_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all profiles for current user."""
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == current_user.id)
        .order_by(Profile.created_at.desc())
    )
    profiles = result.scalars().all()
    return profiles


@router.post("/profiles", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new profile for current user."""
    # Create profile
    profile = Profile(
        user_id=current_user.id,
        name=profile_data.name,
        description=profile_data.description,
        settings=profile_data.settings or {}
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return profile


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific profile."""
    result = await db.execute(
        select(Profile)
        .where(Profile.id == profile_id)
        .where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )

    return profile


@router.put("/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: int,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a profile."""
    # Check profile exists and belongs to user
    result = await db.execute(
        select(Profile)
        .where(Profile.id == profile_id)
        .where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )

    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    if update_data:
        for field, value in update_data.items():
            setattr(profile, field, value)

        await db.commit()
        await db.refresh(profile)

    return profile


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a profile."""
    # Check profile exists and belongs to user
    result = await db.execute(
        select(Profile)
        .where(Profile.id == profile_id)
        .where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )

    await db.delete(profile)
    await db.commit()

    return None
