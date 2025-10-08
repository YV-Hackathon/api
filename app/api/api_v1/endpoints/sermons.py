from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import (
    Sermon, SermonCreate, SermonUpdate, SermonWithSpeaker,
    SermonRecommendationsResponse, SermonRecommendation, SpeakerInfo
)

router = APIRouter()

@router.get("/", response_model=List[SermonWithSpeaker])
def get_sermons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    speaker_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all sermons with optional filtering"""
    query = db.query(models.Sermon)
    
    if speaker_id:
        query = query.filter(models.Sermon.speaker_id == speaker_id)
    
    sermons = query.offset(skip).limit(limit).all()
    return sermons

@router.get("/{sermon_id}", response_model=SermonWithSpeaker)
def get_sermon(sermon_id: int, db: Session = Depends(get_db)):
    """Get a specific sermon by ID with speaker information"""
    sermon = db.query(models.Sermon).filter(models.Sermon.id == sermon_id).first()
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    return sermon

@router.post("/", response_model=Sermon)
def create_sermon(sermon: SermonCreate, db: Session = Depends(get_db)):
    """Create a new sermon"""
    # Verify that the speaker exists
    speaker = db.query(models.Speaker).filter(models.Speaker.id == sermon.speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    db_sermon = models.Sermon(**sermon.dict())
    db.add(db_sermon)
    db.commit()
    db.refresh(db_sermon)
    return db_sermon

@router.put("/{sermon_id}", response_model=Sermon)
def update_sermon(
    sermon_id: int, 
    sermon_update: SermonUpdate, 
    db: Session = Depends(get_db)
):
    """Update a sermon"""
    db_sermon = db.query(models.Sermon).filter(models.Sermon.id == sermon_id).first()
    if not db_sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    
    update_data = sermon_update.dict(exclude_unset=True)
    
    # If speaker_id is being updated, verify the speaker exists
    if "speaker_id" in update_data:
        speaker = db.query(models.Speaker).filter(models.Speaker.id == update_data["speaker_id"]).first()
        if not speaker:
            raise HTTPException(status_code=404, detail="Speaker not found")
    
    for field, value in update_data.items():
        setattr(db_sermon, field, value)
    
    db.commit()
    db.refresh(db_sermon)
    return db_sermon

@router.delete("/{sermon_id}")
def delete_sermon(sermon_id: int, db: Session = Depends(get_db)):
    """Delete a sermon"""
    db_sermon = db.query(models.Sermon).filter(models.Sermon.id == sermon_id).first()
    if not db_sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    
    db.delete(db_sermon)
    db.commit()
    return {"message": "Sermon deleted successfully"}

@router.get("/speaker/{speaker_id}/sermons", response_model=List[Sermon])
def get_speaker_sermons(speaker_id: int, db: Session = Depends(get_db)):
    """Get all sermons for a specific speaker"""
    # Verify that the speaker exists
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    sermons = db.query(models.Sermon).filter(models.Sermon.speaker_id == speaker_id).all()
    return sermons

@router.get("/recommendations/{user_id}", response_model=SermonRecommendationsResponse)
def get_sermon_recommendations(
    user_id: int, 
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get 10 recommended sermon clips for a user based on their preferences"""
    # Verify that the user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get sermons with their speakers
    sermons = db.query(models.Sermon).join(models.Speaker).limit(limit).all()
    
    # Convert to response format with mock matching preferences
    recommendations = []
    for sermon in sermons:
        # Create mock matching preferences based on user preferences
        matching_preferences = []
        if user.teaching_style_preference and user.teaching_style_preference == sermon.speaker.teaching_style:
            matching_preferences.append(f"Teaching style: {sermon.speaker.teaching_style.value}")
        if user.bible_reading_preference and user.bible_reading_preference == sermon.speaker.bible_approach:
            matching_preferences.append(f"Bible approach: {sermon.speaker.bible_approach.value}")
        if user.environment_preference and user.environment_preference == sermon.speaker.environment_style:
            matching_preferences.append(f"Environment style: {sermon.speaker.environment_style.value}")
        if user.gender_preference and user.gender_preference == sermon.speaker.gender:
            matching_preferences.append(f"Gender preference: {sermon.speaker.gender.value}")
        
        # If no matches, add some generic preferences
        if not matching_preferences:
            matching_preferences = ["Content relevance", "Speaker style"]
        
        speaker_info = SpeakerInfo(
            id=sermon.speaker.id,
            name=sermon.speaker.name,
            title=sermon.speaker.title,
            teaching_style=sermon.speaker.teaching_style,
            bible_approach=sermon.speaker.bible_approach,
            environment_style=sermon.speaker.environment_style,
            gender=sermon.speaker.gender
        )
        
        recommendation = SermonRecommendation(
            sermon_id=sermon.id,
            title=sermon.title,
            description=sermon.description,
            gcs_url=sermon.gcs_url,
            speaker=speaker_info,
            matching_preferences=matching_preferences,
            recommendation_score=0.85  # Mock score
        )
        recommendations.append(recommendation)
    
    # Get user preferences for context
    user_preferences = {
        "teaching_style_preference": user.teaching_style_preference,
        "bible_reading_preference": user.bible_reading_preference,
        "environment_preference": user.environment_preference,
        "gender_preference": user.gender_preference
    }
    
    return SermonRecommendationsResponse(
        recommendations=recommendations,
        total_count=len(recommendations),
        user_preferences=user_preferences
    )
