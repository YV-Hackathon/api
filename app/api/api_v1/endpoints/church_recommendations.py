from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.services.ai_embedding_service import get_ai_service

router = APIRouter()

@router.get("/recommendations/{user_id}")
def get_church_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of church recommendations"),
    min_ratings: int = Query(3, ge=1, description="Minimum sermon ratings required for recommendations"),
    force_refresh: bool = Query(False, description="Force refresh of AI recommendations"),
    db: Session = Depends(get_db)
):
    """Get personalized church recommendations using AI embeddings
    
    This endpoint uses AI embeddings to provide intelligent church recommendations:
    
    **AI Embedding Approach**:
    - Uses semantic similarity between user preferences and speaker characteristics
    - Leverages AI embeddings for nuanced matching based on teaching style, content, and approach
    - Learns from user feedback on sermon preferences to improve recommendations
    - Analyzes liked/disliked speakers from sermon clips to understand user preferences
    - Aggregates speaker compatibility into church recommendations with detailed explanations
    
    Returns churches ranked by AI-calculated compatibility score with detailed reasoning.
    """
    
    # Verify user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has completed onboarding
    if not user.onboarding_completed:
        raise HTTPException(
            status_code=400, 
            detail="User must complete onboarding before getting church recommendations"
        )
    
    # Check if user has enough sermon ratings
    rating_count = db.query(models.UserSermonPreference).filter(
        models.UserSermonPreference.user_id == user_id
    ).count()
    
    if rating_count < min_ratings:
        raise HTTPException(
            status_code=400,
            detail=f"User needs at least {min_ratings} sermon ratings before getting church recommendations. Current: {rating_count}"
        )
    
    # Get AI-powered church recommendations
    ai_service = get_ai_service()
    
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI recommendation service is currently unavailable"
        )
    
    try:
        # Use AI embeddings for church recommendations
        church_recommendations = ai_service.get_church_recommendations(user, db, limit)
        
        if not church_recommendations:
            # Fallback to basic recommendations if AI fails
            church_recommendations = _get_fallback_church_recommendations(user, db, limit)
        
        # Format response
        response = {
            "user_id": user_id,
            "total_recommendations": len(church_recommendations),
            "user_summary": {
                "onboarding_completed": user.onboarding_completed,
                "sermon_ratings_count": rating_count,
                "preferences": {
                    "teaching_style": user.teaching_style_preference.value if user.teaching_style_preference else None,
                    "bible_approach": user.bible_reading_preference.value if user.bible_reading_preference else None,
                    "environment": user.environment_preference.value if user.environment_preference else None,
                    "gender_preference": user.gender_preference.value if user.gender_preference else None
                }
            },
            "recommendations": church_recommendations
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating church recommendations: {str(e)}"
        )

@router.get("/recommendations/{user_id}/analysis")
def get_user_preference_analysis(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed analysis of user's preferences based on their sermon ratings
    
    This endpoint provides insights into:
    - Which speakers the user likes/dislikes
    - Patterns in user preferences
    - Readiness for church recommendations
    """
    
    # Verify user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's sermon ratings
    ratings = db.query(models.UserSermonPreference).filter(
        models.UserSermonPreference.user_id == user_id
    ).all()
    
    # Analyze ratings
    liked_speakers = []
    disliked_speakers = []
    liked_churches = set()
    
    for rating in ratings:
        speaker_info = {
            "id": rating.sermon.speaker.id,
            "name": rating.sermon.speaker.name,
            "church": rating.sermon.speaker.church.name if rating.sermon.speaker.church else "Independent",
            "teaching_style": rating.sermon.speaker.teaching_style.value if rating.sermon.speaker.teaching_style else None,
            "bible_approach": rating.sermon.speaker.bible_approach.value if rating.sermon.speaker.bible_approach else None,
            "environment_style": rating.sermon.speaker.environment_style.value if rating.sermon.speaker.environment_style else None,
            "sermon_title": rating.sermon.title
        }
        
        if rating.preference == 'thumbs_up':
            liked_speakers.append(speaker_info)
            if rating.sermon.speaker.church_id:
                liked_churches.add(rating.sermon.speaker.church_id)
        elif rating.preference == 'thumbs_down':
            disliked_speakers.append(speaker_info)
    
    # Calculate readiness for church recommendations
    total_ratings = len(ratings)
    min_ratings_needed = 3
    ready_for_churches = total_ratings >= min_ratings_needed
    
    analysis = {
        "user_id": user_id,
        "rating_summary": {
            "total_ratings": total_ratings,
            "liked_sermons": len(liked_speakers),
            "disliked_sermons": len(disliked_speakers),
            "ready_for_church_recommendations": ready_for_churches,
            "ratings_needed": max(0, min_ratings_needed - total_ratings)
        },
        "preference_patterns": {
            "liked_speakers": liked_speakers,
            "disliked_speakers": disliked_speakers,
            "churches_with_liked_speakers": len(liked_churches)
        },
        "stated_preferences": {
            "teaching_style": user.teaching_style_preference.value if user.teaching_style_preference else None,
            "bible_approach": user.bible_reading_preference.value if user.bible_reading_preference else None,
            "environment": user.environment_preference.value if user.environment_preference else None,
            "gender_preference": user.gender_preference.value if user.gender_preference else None
        }
    }
    
    return analysis

def _get_fallback_church_recommendations(user: models.User, db: Session, limit: int) -> List[dict]:
    """Fallback church recommendations when AI is unavailable"""
    
    # Simple rule-based recommendations based on user preferences
    query = db.query(models.Church).filter(models.Church.is_active == True)
    
    # Get churches with speakers matching user preferences
    if user.teaching_style_preference or user.bible_reading_preference or user.environment_preference:
        churches_with_compatible_speakers = db.query(models.Church.id).join(models.Speaker).filter(
            models.Church.is_active == True
        )
        
        if user.teaching_style_preference:
            churches_with_compatible_speakers = churches_with_compatible_speakers.filter(
                models.Speaker.teaching_style == user.teaching_style_preference
            )
        
        if user.bible_reading_preference:
            churches_with_compatible_speakers = churches_with_compatible_speakers.filter(
                models.Speaker.bible_approach == user.bible_reading_preference
            )
        
        if user.environment_preference:
            churches_with_compatible_speakers = churches_with_compatible_speakers.filter(
                models.Speaker.environment_style == user.environment_preference
            )
        
        compatible_church_ids = [c.id for c in churches_with_compatible_speakers.distinct().all()]
        
        if compatible_church_ids:
            query = query.filter(models.Church.id.in_(compatible_church_ids))
    
    churches = query.limit(limit).all()
    
    # Convert to recommendation format
    recommendations = []
    for i, church in enumerate(churches):
        recommendation = {
            'church_id': church.id,
            'church_name': church.name,
            'denomination': church.denomination,
            'description': church.description,
            'address': church.address,
            'website': church.website,
            'image_url': church.image_url,
            'membership_count': church.membership_count,
            'service_times': church.service_times,
            'compatibility_score': 0.5 - (i * 0.05),  # Decreasing score
            'recommendation_reasons': [
                "Preferred",
                church.denomination if church.denomination else "Church",
                "Fallback"
            ]
        }
        recommendations.append(recommendation)
    
    return recommendations

