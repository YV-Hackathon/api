from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum, Table, UniqueConstraint, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.schemas import TeachingStyle, BibleApproach, EnvironmentStyle, TopicCategory, Gender

# Association table for many-to-many relationship between speakers and churches
speaker_church_association = Table(
    'speaker_church_associations',
    Base.metadata,
    Column('speaker_id', Integer, ForeignKey('speakers.id'), primary_key=True),
    Column('church_id', Integer, ForeignKey('churches.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

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
    image_url = Column(String(500))  # URL to church image in GCS
    attributes = Column(ARRAY(String))  # Array of free form strings
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    speakers = relationship("Speaker", back_populates="church")  # One-to-many (home church)
    speaking_pastors = relationship("Speaker", secondary=speaker_church_association, back_populates="speaking_churches")  # Many-to-many
    featured_sermons = relationship("FeaturedSermon", back_populates="church")
    
    def __str__(self):
        return f"{self.name} ({self.denomination})"

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
    teaching_style = Column(SQLEnum(TeachingStyle), default=TeachingStyle.WARM_AND_CONVERSATIONAL)
    bible_approach = Column(SQLEnum(BibleApproach), default=BibleApproach.BALANCED)
    environment_style = Column(SQLEnum(EnvironmentStyle), default=EnvironmentStyle.BLENDED)
    gender = Column(SQLEnum(Gender))
    profile_picture_url = Column(String(500))  # URL to profile picture in GCS
    attributes = Column(ARRAY(String))  # Array of free form strings
    is_recommended = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    church_id = Column(Integer, ForeignKey("churches.id"))
    
    # Relationships
    church = relationship("Church", back_populates="speakers")  # One-to-many (home church)
    speaking_churches = relationship("Church", secondary=speaker_church_association, back_populates="speaking_pastors")  # Many-to-many
    sermons = relationship("Sermon", back_populates="speaker")
    
    def __str__(self):
        return f"{self.name} - {self.title}" if self.title else self.name

class Sermon(Base):
    __tablename__ = "sermons"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    gcs_url = Column(String(500), nullable=False)  # URL to GCS bucket
    is_clip = Column(Boolean, nullable=False, default=True)  # True for clips (onboarding), False for full sermons
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    speaker_id = Column(Integer, ForeignKey("speakers.id"), nullable=False)
    
    # Relationships
    speaker = relationship("Speaker", back_populates="sermons")
    featured_in_churches = relationship("FeaturedSermon", back_populates="sermon")
    
    def __str__(self):
        return self.title

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
    gender_preference = Column(SQLEnum(Gender))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

class UserSpeakerPreference(Base):
    __tablename__ = "user_speaker_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    speaker_id = Column(Integer, ForeignKey("speakers.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    speaker = relationship("Speaker")
    
    def __str__(self):
        return f"User {self.user_id} -> Speaker {self.speaker_id}"

class UserSermonPreference(Base):
    __tablename__ = "user_sermon_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sermon_id = Column(Integer, ForeignKey("sermons.id"), nullable=False, index=True)
    preference = Column(String(15), nullable=False, index=True)  # 'thumbs_up' or 'thumbs_down'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    sermon = relationship("Sermon")
    
    def __str__(self):
        return f"User {self.user_id} -> Sermon {self.sermon_id} ({self.preference})"
    
    # Unique constraint to prevent duplicate preferences for same user-sermon pair
    __table_args__ = (
        UniqueConstraint('user_id', 'sermon_id', name='uq_user_sermon_preference'),
    )

class OnboardingQuestion(Base):
    __tablename__ = "onboarding_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    questions = Column(JSON)  # Store the entire questions structure as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __str__(self):
        return f"Onboarding Questions #{self.id}"

class Recommendations(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    speaker_ids = Column(JSON, nullable=False)  # Array of speaker IDs as JSON
    scores = Column(JSON, nullable=True)  # Optional: Array of recommendation scores as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __str__(self):
        return f"Recommendations for User {self.user_id}"
    
    # Unique constraint to prevent duplicate recommendations for same user
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_recommendations'),
    )

class FeaturedSermon(Base):
    __tablename__ = "featured_sermons"
    
    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id", ondelete="CASCADE"), nullable=False)
    sermon_id = Column(Integer, ForeignKey("sermons.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    church = relationship("Church", back_populates="featured_sermons")
    sermon = relationship("Sermon", back_populates="featured_in_churches")
    
    def __str__(self):
        return f"Featured Sermon #{self.id} (Church {self.church_id} -> Sermon {self.sermon_id})"
    
    # Unique constraint to prevent duplicate featured sermons for same church
    __table_args__ = (
        UniqueConstraint('church_id', 'sermon_id', name='uq_church_sermon_featured'),
    )
