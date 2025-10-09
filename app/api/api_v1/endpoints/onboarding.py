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
    SermonWithSpeakerAndChurch
)

router = APIRouter()

# Static onboarding questions (matching the Strapi structure)
ONBOARDING_QUESTIONS = [
    {
        "id": "bibleReadingPreference",
        "title": "When you listen to a sermon, what do you prefer most?",
        "description": "Select the approach that helps you most",
        "type": "single-select",
        "options": [
            {"value": "Life Application", "label": "Practical, everyday life application"},
            {"value": "More Scripture", "label": "Deep, verse-by-verse Scripture teaching"},
            {"value": "Balanced", "label": "A balance of both"}
        ]
    },
    {
        "id": "teachingStylePreference",
        "title": "Which teaching style helps you connect best?",
        "description": "Choose the teaching style that resonates with you",
        "type": "single-select",
        "options": [
            {"value": "Warm", "label": "Warm and conversational"},
            {"value": "Calm", "label": "Calm and reflective"},
            {"value": "Passionate", "label": "Passionate and high-energy"}
        ]
    },
    {
        "id": "genderPreference",
        "title": "Do you have a preference for who teaches?",
        "description": "Choose the gender that resonates with you",
        "type": "single-select",
        "options": [{"value": "Male", "label": "Male pastor"}, {"value": "Female", "label": "Female pastor"}, {"value": "Either", "label": "No preference"}]
    },
    {
        "id": "environmentPreference",
        "title": "What kind of environment are you hoping to find?",
        "description": "Select the church environment that appeals to you",
        "type": "single-select",
        "options": [
            {"value": "Traditional", "label": "Traditional"},
            {"value": "Contemporary", "label": "Contemporary"},
            {"value": "Blended", "label": "Blended"}
        ]
    },
    {
        "id": "speakers",
        "title": "Select Speakers That Interest You",
        "description": "Choose speakers whose messages resonate with you",
        "type": "multi-select",
        "options": []  # Will be populated dynamically
    },
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
    
    # Handle gender preference mapping from frontend values to enum values
    if answers.gender_preference:
        if answers.gender_preference == "Male":
            user.gender_preference = "MALE"
        elif answers.gender_preference == "Female":
            user.gender_preference = "FEMALE"
        # "Either" means no preference, so we leave it as None
        elif answers.gender_preference == "Either":
            user.gender_preference = None
        else:
            user.gender_preference = answers.gender_preference
    
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
    
    # Get sermons from recommended speakers (limit to 5)
    recommended_sermons = get_recommended_sermons_from_speakers(recommended_speakers, db, limit=5)
    
    # Get user's preferred speakers
    preferred_speakers = db.query(models.Speaker).join(models.UserSpeakerPreference).filter(
        models.UserSpeakerPreference.user_id == submission.user_id
    ).all()
    
    user_dict = user.__dict__.copy()
    user_dict['preferred_speakers'] = preferred_speakers
    
    return OnboardingResponse(
        user=user_dict,
        recommended_sermons=recommended_sermons
    )

@router.get("/recommendations/{user_id}", response_model=List[SermonWithSpeakerAndChurch])
def get_user_recommendations(user_id: int, db: Session = Depends(get_db)):
    """Get personalized sermon recommendations for a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    recommended_speakers = get_recommended_speakers(user, db)
    return get_recommended_sermons_from_speakers(recommended_speakers, db, limit=5)

def get_recommended_speakers(user, db: Session) -> List[models.Speaker]:
    """Get recommended speakers based on user preferences"""
    query = db.query(models.Speaker)
    
    # Filter by user preferences
    if user.teaching_style_preference:
        query = query.filter(models.Speaker.teaching_style == user.teaching_style_preference)
    
    if user.bible_reading_preference:
        query = query.filter(models.Speaker.bible_approach == user.bible_reading_preference)
    
    if user.environment_preference:
        query = query.filter(models.Speaker.environment_style == user.environment_preference)
    
    if user.gender_preference:
        query = query.filter(models.Speaker.gender == user.gender_preference)
    
    # Get recommended speakers
    recommended_speakers = query.all()
    
    # If no matches, return all speakers
    if not recommended_speakers:
        recommended_speakers = db.query(models.Speaker).all()
    
    return recommended_speakers

def get_recommended_sermons_from_speakers(speakers: List[models.Speaker], db: Session, limit: int = 5) -> List[models.Sermon]:
    """Get sermons from recommended speakers with full speaker and church data"""
    if not speakers:
        return []
    
    # Get speaker IDs
    speaker_ids = [speaker.id for speaker in speakers]
    
    # Query sermons from these speakers with speaker and church data included
    # Use joinedload to ensure church data is loaded with the speaker
    from sqlalchemy.orm import joinedload
    
    sermons_query = db.query(models.Sermon).options(
        joinedload(models.Sermon.speaker).joinedload(models.Speaker.church)
    ).filter(
        models.Sermon.speaker_id.in_(speaker_ids),
        models.Sermon.is_clip == True
    ).order_by(models.Sermon.created_at.desc())
    
    # Get the sermons with speaker and church data
    sermons = sermons_query.limit(limit).all()
    
    # If we don't have enough sermons from recommended speakers, fill with others
    if len(sermons) < limit:
        additional_needed = limit - len(sermons)
        existing_sermon_ids = [sermon.id for sermon in sermons]
        
        additional_sermons = db.query(models.Sermon).options(
            joinedload(models.Sermon.speaker).joinedload(models.Speaker.church)
        ).filter(
            ~models.Sermon.id.in_(existing_sermon_ids),
            models.Sermon.is_clip == True
        ).order_by(models.Sermon.created_at.desc()).limit(additional_needed).all()
        
        sermons.extend(additional_sermons)
    
    print(f"✅ Retrieved {len(sermons)} recommended sermons with church data from {len(speakers)} speakers")
    
    # Log church information to verify it's loaded
    for sermon in sermons[:3]:  # Show first 3 for debugging
        church_name = sermon.speaker.church.name if sermon.speaker and sermon.speaker.church else "No Church"
        print(f"   📖 '{sermon.title}' by {sermon.speaker.name} from {church_name}")
    
    return sermons
