from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.schemas import TeachingStyle, BibleApproach, EnvironmentStyle, TopicCategory

class Church(Base):
    __tablename__ = "churches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    denomination = Column(String(100), nullable=False)
    description = Column(Text)
    address = Column(JSON)  # Store as JSON
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    founded_year = Column(Integer)
    membership_count = Column(Integer)
    service_times = Column(JSON)  # Store as JSON
    social_media = Column(JSON)  # Store as JSON
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    speakers = relationship("Speaker", back_populates="church")

class Speaker(Base):
    __tablename__ = "speakers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255), default="")
    bio = Column(Text)
    email = Column(String(255))
    phone = Column(String(50))
    years_of_service = Column(Integer)
    social_media = Column(JSON)  # Store as JSON
    speaking_topics = Column(JSON)  # Store as JSON array
    sort_order = Column(Integer, default=0)
    teaching_style = Column(SQLEnum(TeachingStyle), default=TeachingStyle.BALANCED)
    bible_approach = Column(SQLEnum(BibleApproach), default=BibleApproach.BALANCED)
    environment_style = Column(SQLEnum(EnvironmentStyle), default=EnvironmentStyle.BLENDED)
    is_recommended = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    church_id = Column(Integer, ForeignKey("churches.id"))
    
    # Relationships
    church = relationship("Church", back_populates="speakers")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    bible_reading_preference = Column(SQLEnum(BibleApproach))
    teaching_style_preference = Column(SQLEnum(TeachingStyle))
    environment_preference = Column(SQLEnum(EnvironmentStyle))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserSpeakerPreference(Base):
    __tablename__ = "user_speaker_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    speaker_id = Column(Integer, ForeignKey("speakers.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    speaker = relationship("Speaker")

class OnboardingQuestion(Base):
    __tablename__ = "onboarding_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    questions = Column(JSON)  # Store the entire questions structure as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
