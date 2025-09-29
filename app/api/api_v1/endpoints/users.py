from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import User, UserCreate, UserUpdate, UserWithPreferences

router = APIRouter()

@router.get("/", response_model=List[User])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all users with optional filtering"""
    query = db.query(models.User)
    
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserWithPreferences)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID with preferences"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get preferred speakers
    preferred_speakers = db.query(models.Speaker).join(models.UserSpeakerPreference).filter(
        models.UserSpeakerPreference.user_id == user_id
    ).all()
    
    user_dict = user.__dict__.copy()
    user_dict['preferred_speakers'] = preferred_speakers
    
    return user_dict

@router.post("/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # In a real app, you'd hash the password here
    hashed_password = user.password  # This should be hashed!
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        onboarding_completed=user.onboarding_completed,
        bible_reading_preference=user.bible_reading_preference,
        teaching_style_preference=user.teaching_style_preference,
        environment_preference=user.environment_preference
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db)
):
    """Update a user"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/preferences/speakers")
def update_user_speaker_preferences(
    user_id: int,
    speaker_ids: List[int],
    db: Session = Depends(get_db)
):
    """Update user's preferred speakers"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove existing preferences
    db.query(models.UserSpeakerPreference).filter(
        models.UserSpeakerPreference.user_id == user_id
    ).delete()
    
    # Add new preferences
    for speaker_id in speaker_ids:
        preference = models.UserSpeakerPreference(
            user_id=user_id,
            speaker_id=speaker_id
        )
        db.add(preference)
    
    db.commit()
    return {"message": "Speaker preferences updated successfully"}
