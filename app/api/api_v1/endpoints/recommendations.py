from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import Recommendations, RecommendationsCreate, RecommendationsUpdate
from app.services.recommendation_service import get_ml_service

router = APIRouter()

@router.post("/generate/{user_id}", response_model=Recommendations)
def generate_recommendations(
    user_id: int,
    preferences: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Generate new ML-based speaker recommendations for a user"""
    # Verify that the user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    ml_service = get_ml_service()
    
    # Use provided preferences or extract from user profile
    if not preferences:
        preferences = {
            'trait_choices': [],  # Could be populated from a separate user traits table
            'teaching_style': user.teaching_style_preference,
            'bible_approach': user.bible_reading_preference,
            'environment_style': user.environment_preference,
            'gender_preference': user.gender_preference
        }
    
    # Generate speaker recommendations
    speaker_recs = ml_service.generate_recommendations(preferences, limit=20, db=db)
    
    # Store the recommendations
    stored_recs = ml_service.store_recommendations(db, user_id, speaker_recs)
    
    return stored_recs

@router.get("/{user_id}", response_model=Recommendations)
def get_user_recommendations(user_id: int, db: Session = Depends(get_db)):
    """Get stored recommendations for a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    ml_service = get_ml_service()
    recommendations = ml_service.get_stored_recommendations(db, user_id)
    
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found for user")
    
    return recommendations

@router.put("/{user_id}", response_model=Recommendations)
def update_user_recommendations(
    user_id: int,
    recommendations_update: RecommendationsUpdate,
    db: Session = Depends(get_db)
):
    """Update stored recommendations for a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get existing recommendations
    existing = db.query(models.Recommendations).filter(
        models.Recommendations.user_id == user_id
    ).first()
    
    if not existing:
        # Create new recommendations
        new_recommendations = models.Recommendations(
            user_id=user_id,
            speaker_ids=[int(sid) for sid in recommendations_update.speaker_ids],
            scores=[float(score) for score in recommendations_update.scores] if recommendations_update.scores else None
        )
        db.add(new_recommendations)
    else:
        # Update existing recommendations
        existing.speaker_ids = [int(sid) for sid in recommendations_update.speaker_ids]
        existing.scores = [float(score) for score in recommendations_update.scores] if recommendations_update.scores else None
    
    db.commit()
    
    # Return updated recommendations
    ml_service = get_ml_service()
    return ml_service.get_stored_recommendations(db, user_id)

@router.delete("/{user_id}")
def delete_user_recommendations(user_id: int, db: Session = Depends(get_db)):
    """Delete stored recommendations for a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete recommendations
    deleted_count = db.query(models.Recommendations).filter(
        models.Recommendations.user_id == user_id
    ).delete()
    
    db.commit()
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="No recommendations found for user")
    
    return {"message": "Recommendations deleted successfully"}
