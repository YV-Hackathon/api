from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import (
    SermonPreference, SermonPreferenceCreate, SermonPreferenceUpdate,
    SermonPreferenceWithDetails, SermonPreferencesBatch, SermonPreferenceType
)
from app.services.recommendation_service import trigger_recommendation_update

router = APIRouter()

@router.post("/", response_model=SermonPreference)
def create_sermon_preference(
    preference: SermonPreferenceCreate,
    db: Session = Depends(get_db)
):
    """Create a new sermon preference (thumbs up/down)"""
    # Verify that the user exists
    user = db.query(models.User).filter(models.User.id == preference.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify that the sermon exists
    sermon = db.query(models.Sermon).filter(models.Sermon.id == preference.sermon_id).first()
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    
    # Check if preference already exists
    existing_preference = db.query(models.UserSermonPreference).filter(
        models.UserSermonPreference.user_id == preference.user_id,
        models.UserSermonPreference.sermon_id == preference.sermon_id
    ).first()
    
    if existing_preference:
        # Update existing preference
        existing_preference.preference = preference.preference.value
        db.commit()
        db.refresh(existing_preference)
        
        # Trigger recommendation update
        print(f"🔄 Triggering recommendation update for user {preference.user_id} after preference update")
        trigger_recommendation_update(preference.user_id, db)
        
        return existing_preference
    else:
        # Create new preference
        db_preference = models.UserSermonPreference(
            user_id=preference.user_id,
            sermon_id=preference.sermon_id,
            preference=preference.preference.value
        )
        db.add(db_preference)
        db.commit()
        db.refresh(db_preference)
        
        # Trigger recommendation update
        print(f"🔄 Triggering recommendation update for user {preference.user_id} after new preference")
        trigger_recommendation_update(preference.user_id, db)
        
        return db_preference

@router.post("/batch", response_model=List[SermonPreference])
def create_sermon_preferences_batch(
    batch: SermonPreferencesBatch,
    db: Session = Depends(get_db)
):
    """Create multiple sermon preferences in a single request"""
    # Verify that the user exists
    user = db.query(models.User).filter(models.User.id == batch.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    created_preferences = []
    
    for pref_data in batch.preferences:
        sermon_id = pref_data.get("sermon_id")
        preference = pref_data.get("preference")
        
        if not sermon_id or not preference:
            raise HTTPException(status_code=400, detail="Each preference must have sermon_id and preference")
        
        # Validate preference value
        if preference not in ["thumbs_up", "thumbs_down"]:
            raise HTTPException(status_code=400, detail="Preference must be 'thumbs_up' or 'thumbs_down'")
        
        # Verify that the sermon exists
        sermon = db.query(models.Sermon).filter(models.Sermon.id == sermon_id).first()
        if not sermon:
            raise HTTPException(status_code=404, detail=f"Sermon with id {sermon_id} not found")
        
        # Check if preference already exists
        existing_preference = db.query(models.UserSermonPreference).filter(
            models.UserSermonPreference.user_id == batch.user_id,
            models.UserSermonPreference.sermon_id == sermon_id
        ).first()
        
        if existing_preference:
            # Update existing preference
            existing_preference.preference = preference
            created_preferences.append(existing_preference)
        else:
            # Create new preference
            db_preference = models.UserSermonPreference(
                user_id=batch.user_id,
                sermon_id=sermon_id,
                preference=preference
            )
            db.add(db_preference)
            created_preferences.append(db_preference)
    
    db.commit()
    
    # Refresh all preferences to get updated data
    for pref in created_preferences:
        db.refresh(pref)
    
    # Trigger recommendation update after batch processing
    print(f"🔄 Triggering recommendation update for user {batch.user_id} after batch preference submission ({len(created_preferences)} preferences)")
    trigger_recommendation_update(batch.user_id, db)
    
    return created_preferences

@router.get("/user/{user_id}", response_model=List[SermonPreferenceWithDetails])
def get_user_sermon_preferences(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    preference: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get sermon preferences for a specific user"""
    # Verify that the user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(models.UserSermonPreference).filter(
        models.UserSermonPreference.user_id == user_id
    )
    
    if preference:
        if preference not in ["thumbs_up", "thumbs_down"]:
            raise HTTPException(status_code=400, detail="Preference must be 'thumbs_up' or 'thumbs_down'")
        query = query.filter(models.UserSermonPreference.preference == preference)
    
    preferences = query.offset(skip).limit(limit).all()
    return preferences

@router.get("/sermon/{sermon_id}", response_model=List[SermonPreferenceWithDetails])
def get_sermon_preferences(
    sermon_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    preference: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get preferences for a specific sermon"""
    # Verify that the sermon exists
    sermon = db.query(models.Sermon).filter(models.Sermon.id == sermon_id).first()
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    
    query = db.query(models.UserSermonPreference).filter(
        models.UserSermonPreference.sermon_id == sermon_id
    )
    
    if preference:
        if preference not in ["thumbs_up", "thumbs_down"]:
            raise HTTPException(status_code=400, detail="Preference must be 'thumbs_up' or 'thumbs_down'")
        query = query.filter(models.UserSermonPreference.preference == preference)
    
    preferences = query.offset(skip).limit(limit).all()
    return preferences

@router.put("/{preference_id}", response_model=SermonPreference)
def update_sermon_preference(
    preference_id: int,
    preference_update: SermonPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing sermon preference"""
    preference = db.query(models.UserSermonPreference).filter(
        models.UserSermonPreference.id == preference_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="Sermon preference not found")
    
    preference.preference = preference_update.preference.value
    db.commit()
    db.refresh(preference)
    
    # Trigger recommendation update
    print(f"🔄 Triggering recommendation update for user {preference.user_id} after preference update")
    trigger_recommendation_update(preference.user_id, db)
    
    return preference

@router.delete("/{preference_id}")
def delete_sermon_preference(
    preference_id: int,
    db: Session = Depends(get_db)
):
    """Delete a sermon preference"""
    preference = db.query(models.UserSermonPreference).filter(
        models.UserSermonPreference.id == preference_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="Sermon preference not found")
    
    # Store user_id before deletion for recommendation update
    user_id = preference.user_id
    
    db.delete(preference)
    db.commit()
    
    # Trigger recommendation update after deletion
    print(f"🔄 Triggering recommendation update for user {user_id} after preference deletion")
    trigger_recommendation_update(user_id, db)
    
    return {"message": "Sermon preference deleted successfully"}

@router.get("/user/{user_id}/sermon/{sermon_id}", response_model=Optional[SermonPreferenceWithDetails])
def get_user_sermon_preference(
    user_id: int,
    sermon_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific user's preference for a specific sermon"""
    preference = db.query(models.UserSermonPreference).filter(
        models.UserSermonPreference.user_id == user_id,
        models.UserSermonPreference.sermon_id == sermon_id
    ).first()
    
    return preference
