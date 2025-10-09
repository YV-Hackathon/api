from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
import json

# Enums
class TeachingStyle(str, Enum):
    WARM_AND_CONVERSATIONAL = "WARM_AND_CONVERSATIONAL"
    CALM_AND_REFLECTIVE = "CALM_AND_REFLECTIVE"
    PASSIONATE_AND_HIGH_ENERGY = "PASSIONATE_AND_HIGH_ENERGY"

class BibleApproach(str, Enum):
    MORE_SCRIPTURE = "MORE_SCRIPTURE"
    MORE_APPLICATION = "MORE_APPLICATION"
    BALANCED = "BALANCED"

class EnvironmentStyle(str, Enum):
    TRADITIONAL = "TRADITIONAL"
    CONTEMPORARY = "CONTEMPORARY"
    BLENDED = "BLENDED"

class TopicCategory(str, Enum):
    PREACHING = "PREACHING"
    TEACHING = "TEACHING"
    COUNSELING = "COUNSELING"
    LEADERSHIP = "LEADERSHIP"
    EVANGELISM = "EVANGELISM"
    WORSHIP = "WORSHIP"
    YOUTH = "YOUTH"
    MARRIAGE = "MARRIAGE"
    FAMILY = "FAMILY"
    PRAYER = "PRAYER"
    OTHER = "OTHER"

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

# Base schemas
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str

class ServiceTimes(BaseModel):
    sunday: Optional[List[str]] = None
    monday: Optional[List[str]] = None
    tuesday: Optional[List[str]] = None
    wednesday: Optional[List[str]] = None
    thursday: Optional[List[str]] = None
    friday: Optional[List[str]] = None
    saturday: Optional[List[str]] = None
    weekdays: Optional[List[str]] = None

class SocialMedia(BaseModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    linkedin: Optional[str] = None

class SpeakingTopic(BaseModel):
    name: str
    description: Optional[str] = None
    category: TopicCategory

# Church schemas
class ChurchBase(BaseModel):
    name: str
    denomination: str
    description: Optional[str] = None
    address: Optional[Address] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    founded_year: Optional[int] = None
    membership_count: Optional[int] = None
    service_times: Optional[ServiceTimes] = None
    social_media: Optional[SocialMedia] = None
    image_url: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class ChurchCreate(ChurchBase):
    pass

class ChurchUpdate(BaseModel):
    name: Optional[str] = None
    denomination: Optional[str] = None
    description: Optional[str] = None
    address: Optional[Address] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    founded_year: Optional[int] = None
    membership_count: Optional[int] = None
    service_times: Optional[ServiceTimes] = None
    social_media: Optional[SocialMedia] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class Church(ChurchBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ChurchWithSpeakers(Church):
    speakers: List["Speaker"] = []

# Speaker schemas
class SpeakerBase(BaseModel):
    name: str
    title: Optional[str] = ""
    bio: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    years_of_service: Optional[int] = None
    social_media: Optional[SocialMedia] = None
    speaking_topics: List[SpeakingTopic] = []
    sort_order: int = 0
    teaching_style: TeachingStyle = TeachingStyle.WARM_AND_CONVERSATIONAL
    bible_approach: BibleApproach = BibleApproach.BALANCED
    environment_style: EnvironmentStyle = EnvironmentStyle.BLENDED
    gender: Optional[Gender] = None
    profile_picture_url: Optional[str] = None
    is_recommended: bool = False
    

class SpeakerCreate(SpeakerBase):
    church_id: Optional[int] = None

class SpeakerUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    years_of_service: Optional[int] = None
    social_media: Optional[SocialMedia] = None
    speaking_topics: Optional[List[SpeakingTopic]] = None
    sort_order: Optional[int] = None
    teaching_style: Optional[TeachingStyle] = None
    bible_approach: Optional[BibleApproach] = None
    environment_style: Optional[EnvironmentStyle] = None
    gender: Optional[Gender] = None
    profile_picture_url: Optional[str] = None
    is_recommended: Optional[bool] = None
    church_id: Optional[int] = None

class Speaker(SpeakerBase):
    id: int
    church_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class SpeakerWithChurch(Speaker):
    church: Optional[Church] = None

# Sermon schemas
class SermonBase(BaseModel):
    title: str
    description: Optional[str] = None
    gcs_url: str

class SermonCreate(SermonBase):
    speaker_id: int

class SermonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    gcs_url: Optional[str] = None
    speaker_id: Optional[int] = None

class Sermon(SermonBase):
    id: int
    speaker_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SermonWithSpeaker(Sermon):
    speaker: Optional[Speaker] = None

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    onboarding_completed: bool = False
    bible_reading_preference: Optional[BibleApproach] = None
    teaching_style_preference: Optional[TeachingStyle] = None
    environment_preference: Optional[EnvironmentStyle] = None
    gender_preference: Optional[Gender] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    onboarding_completed: Optional[bool] = None
    bible_reading_preference: Optional[BibleApproach] = None
    teaching_style_preference: Optional[TeachingStyle] = None
    environment_preference: Optional[EnvironmentStyle] = None
    gender_preference: Optional[Gender] = None

class User(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserWithPreferences(User):
    preferred_speakers: List[Speaker] = []

# Onboarding schemas
class OnboardingQuestion(BaseModel):
    id: str
    title: str
    description: str
    type: str  # "single-select" or "multi-select"
    options: List[Dict[str, Any]]

class OnboardingAnswer(BaseModel):
    speakers: Optional[List[int]] = None
    bible_reading_preference: Optional[BibleApproach] = None
    teaching_style_preference: Optional[TeachingStyle] = None
    environment_preference: Optional[EnvironmentStyle] = None

class OnboardingSubmit(BaseModel):
    user_id: int
    answers: OnboardingAnswer

class OnboardingResponse(BaseModel):
    user: UserWithPreferences
    recommended_speakers: List[SpeakerWithChurch]

# Church Followers schemas
class ChurchFollowersBase(BaseModel):
    church_id: int
    user_id: int

class ChurchFollowersCreate(ChurchFollowersBase):
    pass

class ChurchFollowers(ChurchFollowersBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChurchFollowersWithDetails(ChurchFollowers):
    church: Optional[Church] = None
    user: Optional[User] = None

# Simple conversion function for speakers
def convert_speaker_data(speaker_data):
    """Convert speaker data to handle speaking_topics conversion"""
    if hasattr(speaker_data, '__dict__'):
        data = speaker_data.__dict__.copy()
    else:
        data = speaker_data
    
    # Handle speaking_topics conversion
    if 'speaking_topics' in data:
        speaking_topics_raw = data['speaking_topics']
        if speaking_topics_raw is None:
            data['speaking_topics'] = []
        elif isinstance(speaking_topics_raw, str):
            try:
                topics_data = json.loads(speaking_topics_raw)
                if isinstance(topics_data, list):
                    speaking_topics = []
                    for topic_data in topics_data:
                        if isinstance(topic_data, dict):
                            speaking_topics.append(SpeakingTopic(**topic_data))
                    data['speaking_topics'] = speaking_topics
                else:
                    data['speaking_topics'] = []
            except (json.JSONDecodeError, TypeError, ValueError):
                data['speaking_topics'] = []
        elif isinstance(speaking_topics_raw, list):
            # Already a list, convert each item to SpeakingTopic
            speaking_topics = []
            for topic_data in speaking_topics_raw:
                if isinstance(topic_data, dict):
                    speaking_topics.append(SpeakingTopic(**topic_data))
            data['speaking_topics'] = speaking_topics
        else:
            data['speaking_topics'] = []
    
    return data

# Speaker Followers schemas
class SpeakerFollowersBase(BaseModel):
    speaker_id: int
    user_id: int

class SpeakerFollowersCreate(SpeakerFollowersBase):
    pass

class SpeakerFollowers(SpeakerFollowersBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SpeakerFollowersWithDetails(SpeakerFollowers):
    speaker: Optional[Speaker] = None
    user: Optional[User] = None

# Sermon Recommendation schemas
class SpeakerInfo(BaseModel):
    id: int
    name: str
    title: Optional[str] = None
    teaching_style: Optional[TeachingStyle] = None
    bible_approach: Optional[BibleApproach] = None
    environment_style: Optional[EnvironmentStyle] = None
    gender: Optional[Gender] = None

class SermonRecommendation(BaseModel):
    sermon_id: int
    title: str
    description: Optional[str] = None
    gcs_url: str
    speaker: SpeakerInfo
    matching_preferences: List[str] = []
    recommendation_score: float

class SermonRecommendationsResponse(BaseModel):
    recommendations: List[SermonRecommendation]
    total_count: int
    user_preferences: Dict[str, Any] = {}

# Sermon Preference schemas
class SermonPreferenceType(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"

class SermonPreferenceBase(BaseModel):
    user_id: int
    sermon_id: int
    preference: SermonPreferenceType

class SermonPreferenceCreate(SermonPreferenceBase):
    pass

class SermonPreferenceUpdate(BaseModel):
    preference: SermonPreferenceType

class SermonPreference(SermonPreferenceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SermonPreferenceWithDetails(SermonPreference):
    sermon: Optional[Sermon] = None
    user: Optional[User] = None

class SermonPreferencesBatch(BaseModel):
    user_id: int
    preferences: List[Dict[str, Any]]  # List of {"sermon_id": int, "preference": "thumbs_up" or "thumbs_down"}

# Recommendations schemas
class RecommendationsBase(BaseModel):
    user_id: int
    speaker_ids: List[int]
    scores: Optional[List[float]] = None

class RecommendationsCreate(RecommendationsBase):
    pass

class RecommendationsUpdate(BaseModel):
    speaker_ids: List[int]
    scores: Optional[List[float]] = None

class Recommendations(RecommendationsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RecommendationsWithDetails(Recommendations):
    user: Optional[User] = None

# New schemas for speaker-based recommendations
class SpeakerRecommendation(BaseModel):
    speaker_id: int
    speaker_name: str
    church_name: Optional[str] = None
    recommendation_score: Optional[float] = None
    matching_preferences: List[str] = []

class ChurchRecommendation(BaseModel):
    church_id: int
    church_name: str
    denomination: str
    description: Optional[str] = None
    recommended_speakers: List[SpeakerInfo] = []
    recommendation_score: Optional[float] = None

class ChurchRecommendationsResponse(BaseModel):
    recommendations: List[ChurchRecommendation]
    total_count: int
    user_preferences: Dict[str, Any]

# Update forward references
ChurchWithSpeakers.model_rebuild()
SpeakerWithChurch.model_rebuild()
SermonWithSpeaker.model_rebuild()
UserWithPreferences.model_rebuild()
ChurchFollowersWithDetails.model_rebuild()
SpeakerFollowersWithDetails.model_rebuild()
RecommendationsWithDetails.model_rebuild()
