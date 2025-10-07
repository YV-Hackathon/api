from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

# Enums
class TeachingStyle(str, Enum):
    ACADEMIC = "ACADEMIC"
    RELATABLE = "RELATABLE"
    BALANCED = "BALANCED"

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
    teaching_style: TeachingStyle = TeachingStyle.BALANCED
    bible_approach: BibleApproach = BibleApproach.BALANCED
    environment_style: EnvironmentStyle = EnvironmentStyle.BLENDED
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
    is_recommended: Optional[bool] = None
    church_id: Optional[int] = None

class Speaker(SpeakerBase):
    id: int
    church_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

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

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    onboarding_completed: Optional[bool] = None
    bible_reading_preference: Optional[BibleApproach] = None
    teaching_style_preference: Optional[TeachingStyle] = None
    environment_preference: Optional[EnvironmentStyle] = None

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

# Update forward references
ChurchWithSpeakers.model_rebuild()
SpeakerWithChurch.model_rebuild()
SermonWithSpeaker.model_rebuild()
UserWithPreferences.model_rebuild()
