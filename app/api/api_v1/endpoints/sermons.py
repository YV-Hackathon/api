from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import (
    Sermon, SermonCreate, SermonUpdate, SermonWithSpeaker,
    SermonRecommendationsResponse, SermonRecommendation, SpeakerInfo
)
from app.services.recommendation_service import get_ml_service

router = APIRouter()

@router.get("/", response_model=List[SermonWithSpeaker])
def get_sermons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    speaker_id: Optional[int] = None,
    is_clip: Optional[bool] = Query(None, description="Filter by clip status - true for clips, false for full sermons"),
    db: Session = Depends(get_db)
):
    """Get all sermons with optional filtering"""
    query = db.query(models.Sermon)
    
    if speaker_id:
        query = query.filter(models.Sermon.speaker_id == speaker_id)
    
    if is_clip is not None:
        query = query.filter(models.Sermon.is_clip == is_clip)
    
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
def get_speaker_sermons(
    speaker_id: int, 
    is_clip: Optional[bool] = Query(None, description="Filter by clip status - true for clips, false for full sermons"),
    db: Session = Depends(get_db)
):
    """Get all sermons for a specific speaker"""
    # Verify that the speaker exists
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    query = db.query(models.Sermon).filter(models.Sermon.speaker_id == speaker_id)
    
    if is_clip is not None:
        query = query.filter(models.Sermon.is_clip == is_clip)
    
    sermons = query.all()
    return sermons

@router.get("/recommendations/{user_id}", response_model=SermonRecommendationsResponse)
def get_sermon_recommendations(
    user_id: int, 
    limit: int = Query(10, ge=1, le=50),
    refresh: bool = Query(False, description="Force refresh of recommendations"),
    db: Session = Depends(get_db)
):
    """Get recommended sermon clips for a user based on ML model speaker recommendations"""
    # Verify that the user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    ml_service = get_ml_service()
    
    # Get stored recommendations or generate new ones
    stored_recs = ml_service.get_stored_recommendations(db, user_id)
    
    if not stored_recs or refresh:
        # Generate new recommendations using ML model
        user_preferences = {
            'trait_choices': [],  # You can populate this from user preferences
            'teaching_style': user.teaching_style_preference,
            'bible_approach': user.bible_reading_preference,
            'environment_style': user.environment_preference,
            'gender_preference': user.gender_preference
        }
        
        # Generate speaker recommendations
        speaker_recs = ml_service.generate_recommendations(user_preferences, limit=limit*2)  # Get more speakers to have enough sermons
        
        # Store the recommendations
        stored_recs = ml_service.store_recommendations(db, user_id, speaker_recs)
    
    # Get sermons from recommended speakers
    recommended_speaker_ids = stored_recs.speaker_ids[:limit*2] if stored_recs.speaker_ids else []
    
    if recommended_speaker_ids:
        # Get sermon clips from recommended speakers, ordered by recommendation score
        sermons_query = db.query(models.Sermon).join(models.Speaker).filter(
            models.Speaker.id.in_(recommended_speaker_ids),
            models.Sermon.is_clip == True  # Only return clips for recommendations
        )
        
        # Order by speaker recommendation score (if available)
        if stored_recs.scores:
            # Create a mapping of speaker_id to score for ordering
            speaker_score_map = dict(zip(stored_recs.speaker_ids, stored_recs.scores))
            sermons = sermons_query.all()
            # Sort sermons by their speaker's recommendation score
            sermons.sort(key=lambda s: speaker_score_map.get(s.speaker_id, 0), reverse=True)
        else:
            sermons = sermons_query.all()
        
        # Limit to requested number of sermons
        sermons = sermons[:limit]
    else:
        # Fallback: get sermons using basic preference matching
        sermons = _get_fallback_sermon_recommendations(user, db, limit)
    
    # Convert to response format
    recommendations = []
    speaker_score_map = dict(zip(stored_recs.speaker_ids, stored_recs.scores or [])) if stored_recs else {}
    
    for sermon in sermons:
        # Create matching preferences based on user preferences
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
        
        # Get recommendation score from ML model
        recommendation_score = speaker_score_map.get(sermon.speaker_id, 0.5)
        
        recommendation = SermonRecommendation(
            sermon_id=sermon.id,
            title=sermon.title,
            description=sermon.description,
            gcs_url=sermon.gcs_url,
            speaker=speaker_info,
            matching_preferences=matching_preferences,
            recommendation_score=recommendation_score
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


def _get_fallback_sermon_recommendations(user, db: Session, limit: int) -> List[models.Sermon]:
    """Fallback sermon recommendations using basic preference matching."""
    query = db.query(models.Sermon).join(models.Speaker).filter(
        models.Sermon.is_clip == True  # Only return clips for recommendations
    )
    
    # Filter by user preferences
    if user.teaching_style_preference:
        query = query.filter(models.Speaker.teaching_style == user.teaching_style_preference)
    
    if user.bible_reading_preference:
        query = query.filter(models.Speaker.bible_approach == user.bible_reading_preference)
    
    if user.environment_preference:
        query = query.filter(models.Speaker.environment_style == user.environment_preference)
    
    if user.gender_preference:
        query = query.filter(models.Speaker.gender == user.gender_preference)
    
    sermons = query.limit(limit).all()
    
    # If no matches, return any sermon clips
    if not sermons:
        sermons = db.query(models.Sermon).join(models.Speaker).filter(
            models.Sermon.is_clip == True
        ).limit(limit).all()
    
    return sermons
