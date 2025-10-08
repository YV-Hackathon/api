from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import (
    Church, ChurchWithSpeakers, ChurchRecommendation, ChurchRecommendationsResponse, SpeakerInfo
)
from app.services.recommendation_service import get_ml_service

router = APIRouter()

@router.get("/", response_model=List[ChurchWithSpeakers])
def get_churches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    denomination: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all churches with optional filtering"""
    query = db.query(models.Church)
    
    if is_active is not None:
        query = query.filter(models.Church.is_active == is_active)
    
    if denomination:
        query = query.filter(models.Church.denomination.ilike(f"%{denomination}%"))
    
    churches = query.offset(skip).limit(limit).all()
    return churches

@router.get("/{church_id}", response_model=ChurchWithSpeakers)
def get_church(church_id: int, db: Session = Depends(get_db)):
    """Get a specific church by ID with speakers"""
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return church

@router.get("/recommendations/{user_id}", response_model=ChurchRecommendationsResponse)
def get_church_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50),
    refresh: bool = Query(False, description="Force refresh of recommendations"),
    db: Session = Depends(get_db)
):
    """Get recommended churches for a user based on ML model speaker recommendations"""
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
        speaker_recs = ml_service.generate_recommendations(user_preferences, limit=limit*3)  # Get more speakers for variety
        
        # Store the recommendations
        stored_recs = ml_service.store_recommendations(db, user_id, speaker_recs)
    
    # Get churches associated with recommended speakers
    recommended_speaker_ids = stored_recs.speaker_ids if stored_recs.speaker_ids else []
    
    if recommended_speaker_ids:
        # Get churches that have recommended speakers (either as home church or speaking venue)
        churches_query = db.query(models.Church).join(models.Speaker).filter(
            models.Speaker.id.in_(recommended_speaker_ids)
        ).distinct()
        
        churches = churches_query.limit(limit).all()
        
        # Also get churches through speaker associations (many-to-many)
        associated_churches = db.query(models.Church).join(
            models.speaker_church_association
        ).filter(
            models.speaker_church_association.c.speaker_id.in_(recommended_speaker_ids)
        ).distinct().limit(limit).all()
        
        # Combine and deduplicate churches
        all_churches = {church.id: church for church in churches + associated_churches}
        churches = list(all_churches.values())[:limit]
    else:
        # Fallback: get churches using basic preference matching
        churches = _get_fallback_church_recommendations(user, db, limit)
    
    # Convert to response format
    recommendations = []
    speaker_score_map = dict(zip(stored_recs.speaker_ids, stored_recs.scores or [])) if stored_recs else {}
    
    for church in churches:
        # Get recommended speakers associated with this church
        church_speaker_ids = [s.id for s in church.speakers if s.id in recommended_speaker_ids]
        
        # Also check many-to-many associations
        associated_speakers = db.query(models.Speaker).join(
            models.speaker_church_association
        ).filter(
            models.speaker_church_association.c.church_id == church.id,
            models.speaker_church_association.c.speaker_id.in_(recommended_speaker_ids)
        ).all()
        
        church_speaker_ids.extend([s.id for s in associated_speakers])
        church_speaker_ids = list(set(church_speaker_ids))  # Remove duplicates
        
        # Get the recommended speakers for this church
        recommended_speakers = []
        church_recommendation_score = 0.0
        
        for speaker_id in church_speaker_ids:
            speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
            if speaker:
                speaker_score = speaker_score_map.get(speaker_id, 0.5)
                church_recommendation_score = max(church_recommendation_score, speaker_score)
                
                speaker_info = SpeakerInfo(
                    id=speaker.id,
                    name=speaker.name,
                    title=speaker.title,
                    teaching_style=speaker.teaching_style,
                    bible_approach=speaker.bible_approach,
                    environment_style=speaker.environment_style,
                    gender=speaker.gender
                )
                recommended_speakers.append(speaker_info)
        
        # If no recommended speakers, use average score
        if not recommended_speakers and stored_recs.scores:
            church_recommendation_score = sum(stored_recs.scores) / len(stored_recs.scores)
        elif not recommended_speakers:
            church_recommendation_score = 0.5
        
        recommendation = ChurchRecommendation(
            church_id=church.id,
            church_name=church.name,
            denomination=church.denomination,
            description=church.description,
            recommended_speakers=recommended_speakers,
            recommendation_score=church_recommendation_score
        )
        recommendations.append(recommendation)
    
    # Sort by recommendation score
    recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
    
    # Get user preferences for context
    user_preferences = {
        "teaching_style_preference": user.teaching_style_preference,
        "bible_reading_preference": user.bible_reading_preference,
        "environment_preference": user.environment_preference,
        "gender_preference": user.gender_preference
    }
    
    return ChurchRecommendationsResponse(
        recommendations=recommendations,
        total_count=len(recommendations),
        user_preferences=user_preferences
    )


def _get_fallback_church_recommendations(user, db: Session, limit: int) -> List[models.Church]:
    """Fallback church recommendations using basic preference matching."""
    # Get churches that have speakers matching user preferences
    query = db.query(models.Church).join(models.Speaker)
    
    # Filter by user preferences
    if user.teaching_style_preference:
        query = query.filter(models.Speaker.teaching_style == user.teaching_style_preference)
    
    if user.bible_reading_preference:
        query = query.filter(models.Speaker.bible_approach == user.bible_reading_preference)
    
    if user.environment_preference:
        query = query.filter(models.Speaker.environment_style == user.environment_preference)
    
    if user.gender_preference:
        query = query.filter(models.Speaker.gender == user.gender_preference)
    
    churches = query.distinct().limit(limit).all()
    
    # If no matches, return active churches
    if not churches:
        churches = db.query(models.Church).filter(
            models.Church.is_active == True
        ).limit(limit).all()
    
    return churches