from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db import models
from app.models.schemas import (
    OnboardingQuestion, 
    OnboardingSubmit, 
    OnboardingResponse,
    UserWithPreferences,
    SpeakerWithChurch
)

router = APIRouter()

# Static onboarding questions (matching the Strapi structure)
ONBOARDING_QUESTIONS = [
    {
        "id": "speakers",
        "title": "Select Speakers That Interest You",
        "description": "Choose speakers whose messages resonate with you",
        "type": "multi-select",
        "options": []  # Will be populated dynamically
    },
    {
        "id": "bibleReadingPreference",
        "title": "When you read the Bible, what's most helpful for you?",
        "description": "Select the approach that helps you most",
        "type": "single-select",
        "options": [
            {"value": "More Scripture", "label": "Focused on reading large sections of the text"},
            {"value": "Life Application", "label": "Practical guidance for everyday life"},
            {"value": "Balanced", "label": "A mix of both Scripture and life application"}
        ]
    },
    {
        "id": "teachingStylePreference",
        "title": "What style of teaching do you connect with most?",
        "description": "Choose the teaching style that resonates with you",
        "type": "single-select",
        "options": [
            {"value": "Academic", "label": "In-depth explanations and context"},
            {"value": "Relatable", "label": "Everyday examples that connect to your life"},
            {"value": "Balanced", "label": "A balance of depth and accessibility"}
        ]
    },
    {
        "id": "environmentPreference",
        "title": "What kind of environment are you hoping to find?",
        "description": "Select the church environment that appeals to you",
        "type": "single-select",
        "options": [
            {"value": "Traditional", "label": "Hymns, liturgy and structured services"},
            {"value": "Contemporary", "label": "Modern worship and casual style"},
            {"value": "Blended", "label": "A mix of traditional and modern services"}
        ]
    }
]

@router.get("/questions", response_model=List[OnboardingQuestion])
def get_onboarding_questions(db: Session = Depends(get_db)):
    """Get onboarding questions with dynamic speaker options"""
    # Get all speakers for the speaker selection question
    speakers = db.query(models.Speaker).all()
    
    # Create speaker options
    speaker_options = []
    for speaker in speakers:
        option = {
            "value": str(speaker.id),
            "label": speaker.name,
            "subtitle": speaker.title,
            "church": speaker.church.name if speaker.church else "No Church",
            "profile_picture_url": speaker.profile_picture_url
        }
        speaker_options.append(option)
    
    # Update the speakers question with dynamic options
    questions = ONBOARDING_QUESTIONS.copy()
    for question in questions:
        if question["id"] == "speakers":
            question["options"] = speaker_options
    
    return questions

@router.post("/submit", response_model=OnboardingResponse)
def submit_onboarding_answers(
    submission: OnboardingSubmit,
    db: Session = Depends(get_db)
):
    """Submit user's onboarding answers and get recommendations"""
    # Get user
    user = db.query(models.User).filter(models.User.id == submission.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user preferences
    answers = submission.answers
    user.bible_reading_preference = answers.bible_reading_preference
    user.teaching_style_preference = answers.teaching_style_preference
    user.environment_preference = answers.environment_preference
    user.onboarding_completed = True
    
    # Update speaker preferences
    if answers.speakers:
        # Remove existing preferences
        db.query(models.UserSpeakerPreference).filter(
            models.UserSpeakerPreference.user_id == submission.user_id
        ).delete()
        
        # Add new preferences
        for speaker_id in answers.speakers:
            preference = models.UserSpeakerPreference(
                user_id=submission.user_id,
                speaker_id=speaker_id
            )
            db.add(preference)
    
    db.commit()
    db.refresh(user)
    
    # Get recommended speakers based on preferences
    recommended_speakers = get_recommended_speakers(user, db)
    
    # Get user's preferred speakers
    preferred_speakers = db.query(models.Speaker).join(models.UserSpeakerPreference).filter(
        models.UserSpeakerPreference.user_id == submission.user_id
    ).all()
    
    user_dict = user.__dict__.copy()
    user_dict['preferred_speakers'] = preferred_speakers
    
    return OnboardingResponse(
        user=user_dict,
        recommended_speakers=recommended_speakers
    )

@router.get("/recommendations/{user_id}", response_model=List[SpeakerWithChurch])
def get_user_recommendations(user_id: int, db: Session = Depends(get_db)):
    """Get personalized recommendations for a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return get_recommended_speakers(user, db)

def get_recommended_speakers(user, db: Session) -> List[SpeakerWithChurch]:
    """Get recommended speakers based on user preferences"""
    query = db.query(models.Speaker)
    
    # Filter by user preferences
    if user.teaching_style_preference:
        query = query.filter(models.Speaker.teaching_style == user.teaching_style_preference)
    
    if user.bible_reading_preference:
        query = query.filter(models.Speaker.bible_approach == user.bible_reading_preference)
    
    if user.environment_preference:
        query = query.filter(models.Speaker.environment_style == user.environment_preference)
    
    # Get recommended speakers
    recommended_speakers = query.all()
    
    # If no matches, return all speakers
    if not recommended_speakers:
        recommended_speakers = db.query(models.Speaker).all()
    
    return recommended_speakers
