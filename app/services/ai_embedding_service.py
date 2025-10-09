"""
AI-Powered Embedding Service for Speaker and Sermon Recommendations

This service uses sentence transformers to create semantic embeddings of speakers
and user preferences, enabling AI-powered recommendations based on meaning rather
than just categorical matching.
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ sentence-transformers not installed. Install with: pip install sentence-transformers")

from app.db import models
from app.models.schemas import TeachingStyle, BibleApproach, EnvironmentStyle, Gender


class AIEmbeddingService:
    """AI service for generating and managing speaker/sermon embeddings"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize the AI embedding service
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model = None
        self.model_name = model_name
        self.speaker_embeddings = {}
        self.cache_dir = Path(__file__).parent.parent.parent / "ai_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                print(f"✅ AI model '{model_name}' loaded successfully")
            except Exception as e:
                print(f"⚠️ Failed to load AI model: {e}")
                self.model = None
        else:
            print("⚠️ Sentence transformers not available, using fallback recommendations")
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.model is not None
    
    def prepare_speaker_text(self, speaker: models.Speaker) -> str:
        """Convert speaker data into descriptive text for AI processing"""
        
        # Handle speaking topics
        topics_text = ""
        if hasattr(speaker, 'speaking_topics') and speaker.speaking_topics:
            try:
                if isinstance(speaker.speaking_topics, str):
                    topics_data = json.loads(speaker.speaking_topics)
                    if isinstance(topics_data, list):
                        topics_text = ', '.join([topic.get('name', '') for topic in topics_data if isinstance(topic, dict)])
                elif isinstance(speaker.speaking_topics, list):
                    topics_text = ', '.join([topic.get('name', '') for topic in speaker.speaking_topics if isinstance(topic, dict)])
            except (json.JSONDecodeError, AttributeError):
                topics_text = ""
        
        # Convert enums to readable text
        teaching_style_text = self._enum_to_text(speaker.teaching_style, {
            TeachingStyle.WARM_AND_CONVERSATIONAL: "warm, conversational, and relatable",
            TeachingStyle.PASSIONATE_AND_HIGH_ENERGY: "passionate, energetic, and dynamic",
            TeachingStyle.CALM_AND_REFLECTIVE: "calm, thoughtful, and reflective"
        })
        
        bible_approach_text = self._enum_to_text(speaker.bible_approach, {
            BibleApproach.MORE_SCRIPTURE: "deep biblical study and scriptural analysis",
            BibleApproach.MORE_APPLICATION: "practical life application and real-world examples",
            BibleApproach.BALANCED: "balanced approach combining scripture study and practical application"
        })
        
        environment_text = self._enum_to_text(speaker.environment_style, {
            EnvironmentStyle.TRADITIONAL: "traditional worship with hymns and formal liturgy",
            EnvironmentStyle.CONTEMPORARY: "contemporary worship with modern music and casual atmosphere",
            EnvironmentStyle.BLENDED: "blended worship combining traditional and contemporary elements"
        })
        
        gender_text = self._enum_to_text(speaker.gender, {
            Gender.MALE: "male",
            Gender.FEMALE: "female"
        })
        
        # Build comprehensive speaker description with enhanced context
        speaker_text = f"""
        {speaker.name} is a {speaker.title or 'speaker'} {f"at {speaker.church.name}" if speaker.church else "in independent ministry"}.
        
        Background: {speaker.bio or 'Experienced speaker and teacher with a heart for ministry and spiritual growth'}
        
        Teaching Style: {speaker.name} communicates with a {teaching_style_text} approach, making messages accessible and engaging.
        
        Biblical Approach: They focus on {bible_approach_text}, helping people understand and apply God's word.
        
        Ministry Environment: {speaker.name} ministers in {environment_text}, creating an atmosphere that connects with their audience.
        
        Speaking Topics: {topics_text or 'Faith, spiritual growth, Christian living, biblical wisdom, and practical discipleship'}
        
        Church Context: {speaker.church.name if speaker.church else 'Independent ministry'} 
        {f"({speaker.church.denomination})" if speaker.church and speaker.church.denomination else ""}
        {f"- {speaker.church.description}" if speaker.church and speaker.church.description else ""}
        
        Gender: {gender_text} speaker
        
        Ministry Impact: {"This speaker is highly recommended for their impactful ministry and transformative teaching" if speaker.is_recommended else "Known for authentic, biblical teaching that connects with diverse audiences"}
        
        Years of Experience: {f"{speaker.years_of_service} years in ministry" if speaker.years_of_service else "Experienced in pastoral ministry and teaching"}
        """.strip()
        
        return speaker_text
    
    def _enum_to_text(self, enum_value, mapping: Dict) -> str:
        """Convert enum to human-readable text"""
        if enum_value and enum_value in mapping:
            return mapping[enum_value]
        return "authentic and meaningful"
    
    def prepare_user_preference_text(self, user: models.User, selected_speakers: List[str] = None) -> str:
        """Convert user preferences into descriptive text for AI processing"""
        
        # Convert preferences to readable text
        bible_pref_text = self._enum_to_text(user.bible_reading_preference, {
            BibleApproach.MORE_SCRIPTURE: "deep biblical study and scriptural analysis",
            BibleApproach.MORE_APPLICATION: "practical life application and real-world examples", 
            BibleApproach.BALANCED: "balanced approach combining scripture study and practical application"
        })
        
        teaching_pref_text = self._enum_to_text(user.teaching_style_preference, {
            TeachingStyle.WARM_AND_CONVERSATIONAL: "warm, conversational, and relatable teaching",
            TeachingStyle.PASSIONATE_AND_HIGH_ENERGY: "passionate, energetic, and dynamic presentations",
            TeachingStyle.CALM_AND_REFLECTIVE: "calm, thoughtful, and reflective communication"
        })
        
        environment_pref_text = self._enum_to_text(user.environment_preference, {
            EnvironmentStyle.TRADITIONAL: "traditional worship with hymns and formal services",
            EnvironmentStyle.CONTEMPORARY: "contemporary worship with modern music and casual atmosphere",
            EnvironmentStyle.BLENDED: "blended worship combining traditional and contemporary elements"
        })
        
        gender_pref_text = self._enum_to_text(user.gender_preference, {
            Gender.MALE: "male speakers",
            Gender.FEMALE: "female speakers"
        })
        
        # Build user preference description
        user_text = f"""
        User Preferences for Spiritual Content:
        
        Bible Study Approach: This person prefers {bible_pref_text} when engaging with scripture and spiritual content.
        
        Teaching Style: They connect best with {teaching_pref_text} that resonates with their learning style.
        
        Worship Environment: They feel most comfortable in {environment_pref_text} settings.
        
        {f"Speaker Gender Preference: They prefer {gender_pref_text}." if user.gender_preference else ""}
        
        {f"Selected Speakers of Interest: {', '.join(selected_speakers)}" if selected_speakers else ""}
        
        Looking for: Inspiring, authentic spiritual content that helps with personal growth, faith development, and practical Christian living.
        """.strip()
        
        return user_text
    
    def generate_speaker_embeddings(self, db: Session) -> Dict[int, np.ndarray]:
        """Generate AI embeddings for all speakers"""
        if not self.is_available():
            return {}
        
        print("🤖 Generating AI embeddings for speakers...")
        
        # Get all speakers with their relationships loaded
        speakers = db.query(models.Speaker).all()
        embeddings = {}
        
        for speaker in speakers:
            try:
                speaker_text = self.prepare_speaker_text(speaker)
                embedding = self.model.encode(speaker_text)
                embeddings[speaker.id] = embedding
                print(f"✅ Generated embedding for {speaker.name}")
            except Exception as e:
                print(f"⚠️ Failed to generate embedding for {speaker.name}: {e}")
        
        # Cache the embeddings
        self.speaker_embeddings = embeddings
        self._save_embeddings_to_cache()
        
        print(f"🎯 Generated {len(embeddings)} speaker embeddings")
        return embeddings
    
    def _save_embeddings_to_cache(self):
        """Save embeddings to cache file"""
        try:
            cache_file = self.cache_dir / "speaker_embeddings.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(self.speaker_embeddings, f)
            print(f"💾 Cached embeddings to {cache_file}")
        except Exception as e:
            print(f"⚠️ Failed to cache embeddings: {e}")
    
    def _load_embeddings_from_cache(self) -> bool:
        """Load embeddings from cache file"""
        try:
            cache_file = self.cache_dir / "speaker_embeddings.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    self.speaker_embeddings = pickle.load(f)
                print(f"📂 Loaded {len(self.speaker_embeddings)} embeddings from cache")
                return True
        except Exception as e:
            print(f"⚠️ Failed to load cached embeddings: {e}")
        return False
    
    def get_ai_recommendations(
        self, 
        user: models.User, 
        selected_speakers: List[str] = None,
        limit: int = 10,
        force_refresh: bool = False,
        db: Session = None
    ) -> List[Tuple[int, float]]:
        """Get AI-powered speaker recommendations based on user preferences
        
        Args:
            user: User object with preferences
            selected_speakers: List of speaker names selected by user
            limit: Maximum number of recommendations
            force_refresh: Force regeneration even if cached
            db: Database session to filter speakers with sermons
        
        Returns:
            List of (speaker_id, similarity_score) tuples
        """
        
        if not self.is_available():
            return []
        
        # Load cached embeddings if not in memory
        if not self.speaker_embeddings:
            if not self._load_embeddings_from_cache():
                print("⚠️ No cached embeddings found. Generate embeddings first.")
                return []
        
        try:
            # Generate user preference embedding
            user_text = self.prepare_user_preference_text(user, selected_speakers)
            user_embedding = self.model.encode(user_text)
            
            # Get speakers who have sermons (if db session provided)
            speakers_with_sermons = set()
            if db:
                speakers_with_sermons_query = db.query(models.Speaker.id).join(models.Sermon).distinct()
                speakers_with_sermons = {speaker.id for speaker in speakers_with_sermons_query.all()}
                print(f"🎯 Found {len(speakers_with_sermons)} speakers with sermons")
            
            # Calculate similarities with all speakers
            similarities = []
            for speaker_id, speaker_embedding in self.speaker_embeddings.items():
                # Skip speakers without sermons if we have DB access
                if db and speakers_with_sermons and speaker_id not in speakers_with_sermons:
                    continue
                    
                similarity = cosine_similarity([user_embedding], [speaker_embedding])[0][0]
                similarities.append((speaker_id, float(similarity)))
            
            # Sort by similarity score (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top recommendations
            return similarities[:limit]
            
        except Exception as e:
            print(f"⚠️ Error generating AI recommendations: {e}")
            return []
    
    def store_ai_recommendations(
        self,
        db: Session,
        user_id: int,
        ai_recommendations: List[Tuple[int, float]],
        recommendation_type: str = "ai_embedding"
    ) -> models.Recommendations:
        """Store AI recommendations in the database
        
        Args:
            db: Database session
            user_id: User ID
            ai_recommendations: List of (speaker_id, score) tuples from AI
            recommendation_type: Type identifier for the recommendation method
            
        Returns:
            Stored Recommendations object
        """
        speaker_ids = [int(rec[0]) for rec in ai_recommendations]
        scores = [float(rec[1]) for rec in ai_recommendations]
        
        # Check if recommendations already exist for this user
        existing = db.query(models.Recommendations).filter(
            models.Recommendations.user_id == user_id
        ).first()
        
        if existing:
            # Update existing recommendations with AI results
            existing.speaker_ids = speaker_ids
            existing.scores = scores
            # Could add a field to track recommendation_type in future
            db.commit()
            db.refresh(existing)
            print(f"✅ Updated AI recommendations for user {user_id}")
            return existing
        else:
            # Create new recommendations
            new_recommendations = models.Recommendations(
                user_id=user_id,
                speaker_ids=speaker_ids,
                scores=scores
            )
            db.add(new_recommendations)
            db.commit()
            db.refresh(new_recommendations)
            print(f"✅ Stored new AI recommendations for user {user_id}")
            return new_recommendations
    
    def get_stored_ai_recommendations(
        self,
        db: Session,
        user_id: int
    ) -> Optional[models.Recommendations]:
        """Get stored AI recommendations from database
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Recommendations object or None if not found
        """
        return db.query(models.Recommendations).filter(
            models.Recommendations.user_id == user_id
        ).first()
    
    def get_ai_recommendations_with_learning(
        self, 
        user: models.User, 
        selected_speakers: List[str] = None,
        limit: int = 10,
        force_refresh: bool = False,
        db: Session = None
    ) -> List[Tuple[int, float]]:
        """Get AI-powered speaker recommendations that learn from user ratings
        
        Args:
            user: User object with preferences
            selected_speakers: List of speaker names selected by user
            limit: Maximum number of recommendations
            force_refresh: Force regeneration even if cached
            db: Database session for accessing sermon ratings
        
        Returns:
            List of (speaker_id, similarity_score) tuples enhanced by learning
        """
        
        if not self.is_available():
            return []
        
        # Load cached embeddings if not in memory
        if not self.speaker_embeddings:
            if not self._load_embeddings_from_cache():
                print("⚠️ No cached embeddings found. Generate embeddings first.")
                return []
        
        try:
            # Get user's sermon ratings for learning
            user_ratings = []
            if db:
                ratings = db.query(models.UserSermonPreference).filter(
                    models.UserSermonPreference.user_id == user.id
                ).all()
                
                for rating in ratings:
                    user_ratings.append({
                        'sermon_id': rating.sermon_id,
                        'speaker_id': rating.sermon.speaker_id,
                        'preference': rating.preference,
                        'speaker_name': rating.sermon.speaker.name
                    })
                
                print(f"🧠 Learning from {len(user_ratings)} user ratings")
            
            # Generate enhanced user preference embedding with learning
            user_text = self.prepare_user_preference_text_with_learning(
                user, selected_speakers, user_ratings
            )
            user_embedding = self.model.encode(user_text)
            
            # Get speakers who have sermons (if db session provided)
            speakers_with_sermons = set()
            if db:
                speakers_with_sermons_query = db.query(models.Speaker.id).join(models.Sermon).distinct()
                speakers_with_sermons = {speaker.id for speaker in speakers_with_sermons_query.all()}
                print(f"🎯 Found {len(speakers_with_sermons)} speakers with sermons")
            
            # Calculate similarities with all speakers
            similarities = []
            for speaker_id, speaker_embedding in self.speaker_embeddings.items():
                # Skip speakers without sermons if we have DB access
                if db and speakers_with_sermons and speaker_id not in speakers_with_sermons:
                    continue
                
                similarity = cosine_similarity([user_embedding], [speaker_embedding])[0][0]
                
                # Apply learning boost/penalty based on user ratings
                learning_adjustment = self._calculate_learning_adjustment(speaker_id, user_ratings)
                adjusted_similarity = similarity + learning_adjustment
                
                similarities.append((speaker_id, float(adjusted_similarity)))
            
            # Sort by adjusted similarity score (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top recommendations
            return similarities[:limit]
            
        except Exception as e:
            print(f"⚠️ Error generating AI recommendations with learning: {e}")
            return []
    
    def prepare_user_preference_text_with_learning(
        self, 
        user: models.User, 
        selected_speakers: List[str] = None, 
        user_ratings: List[Dict] = None
    ) -> str:
        """Enhanced user preference text that incorporates learning from ratings"""
        
        # Start with base preferences
        base_text = self.prepare_user_preference_text(user, selected_speakers)
        
        # Add learning from ratings
        if user_ratings:
            liked_speakers = []
            disliked_speakers = []
            
            for rating in user_ratings:
                if rating['preference'] == 'thumbs_up':
                    liked_speakers.append(rating['speaker_name'])
                elif rating['preference'] == 'thumbs_down':
                    disliked_speakers.append(rating['speaker_name'])
            
            learning_text = ""
            
            if liked_speakers:
                learning_text += f"\n\nSpeakers the user has positively rated: {', '.join(liked_speakers)}. "
                learning_text += "The user enjoys content similar to these speakers and their teaching styles."
            
            if disliked_speakers:
                learning_text += f"\n\nSpeakers the user has negatively rated: {', '.join(disliked_speakers)}. "
                learning_text += "The user prefers content different from these speakers' approaches."
            
            if liked_speakers or disliked_speakers:
                learning_text += "\n\nRecommendations should prioritize speakers similar to those positively rated and avoid those similar to negatively rated speakers."
            
            return base_text + learning_text
        
        return base_text
    
    def _calculate_learning_adjustment(self, speaker_id: int, user_ratings: List[Dict]) -> float:
        """Calculate adjustment to similarity score based on user ratings"""
        
        adjustment = 0.0
        
        for rating in user_ratings:
            if rating['speaker_id'] == speaker_id:
                # Direct rating for this speaker
                if rating['preference'] == 'thumbs_up':
                    adjustment += 0.15  # Strong positive boost
                elif rating['preference'] == 'thumbs_down':
                    adjustment -= 0.20  # Strong negative penalty
            else:
                # Indirect learning from similar speakers
                # This could be enhanced with speaker similarity analysis
                pass
        
        # Cap adjustments to prevent extreme values
        return max(-0.3, min(0.3, adjustment))
    
    def should_refresh_recommendations(
        self,
        stored_recommendations: models.Recommendations,
        max_age_hours: int = 24
    ) -> bool:
        """Check if stored recommendations should be refreshed
        
        Args:
            stored_recommendations: Existing recommendations
            max_age_hours: Maximum age in hours before refresh
            
        Returns:
            True if recommendations should be refreshed
        """
        if not stored_recommendations:
            return True
            
        from datetime import datetime, timedelta
        
        age = datetime.now() - stored_recommendations.updated_at.replace(tzinfo=None)
        return age > timedelta(hours=max_age_hours)
    
    def get_church_recommendations(
        self,
        user: models.User,
        db: Session,
        limit: int = 10
    ) -> List[Dict]:
        """Get church recommendations based on user's liked speakers and preferences
        
        Args:
            user: User object
            db: Database session
            limit: Maximum number of church recommendations
            
        Returns:
            List of church recommendation dictionaries with scores and reasons
        """
        
        if not self.is_available():
            return []
        
        try:
            # Get user's sermon ratings to understand preferences
            user_ratings = db.query(models.UserSermonPreference).filter(
                models.UserSermonPreference.user_id == user.id
            ).all()
            
            # Analyze liked speakers and their churches
            liked_speaker_ids = []
            liked_church_ids = []
            
            for rating in user_ratings:
                if rating.preference == 'thumbs_up':
                    liked_speaker_ids.append(rating.sermon.speaker_id)
                    if rating.sermon.speaker.church_id:
                        liked_church_ids.append(rating.sermon.speaker.church_id)
            
            print(f"🏛️ Analyzing {len(liked_speaker_ids)} liked speakers for church recommendations")
            
            # Get all churches
            all_churches = db.query(models.Church).filter(models.Church.is_active == True).all()
            
            church_scores = []
            
            for church in all_churches:
                score = self._calculate_church_compatibility_score(
                    church, user, liked_speaker_ids, liked_church_ids, db
                )
                
                if score > 0:  # Only include churches with positive scores
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
                        'compatibility_score': score,
                        'recommendation_reasons': self._get_church_recommendation_reasons(
                            church, user, liked_speaker_ids, liked_church_ids, db
                        )
                    }
                    church_scores.append(recommendation)
            
            # Sort by compatibility score
            church_scores.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            return church_scores[:limit]
            
        except Exception as e:
            print(f"⚠️ Error generating church recommendations: {e}")
            return []
    
    def _calculate_church_compatibility_score(
        self,
        church: models.Church,
        user: models.User,
        liked_speaker_ids: List[int],
        liked_church_ids: List[int],
        db: Session
    ) -> float:
        """Calculate compatibility score between user and church"""
        
        score = 0.0
        
        # 1. Direct church preference (user liked speakers from this church)
        if church.id in liked_church_ids:
            score += 0.4  # Strong positive signal
        
        # 2. Speaker compatibility (church has speakers similar to liked ones)
        church_speakers = db.query(models.Speaker).filter(
            models.Speaker.church_id == church.id
        ).all()
        
        if church_speakers and liked_speaker_ids:
            # Check if church speakers match user's preferences
            compatible_speakers = 0
            for speaker in church_speakers:
                # Check teaching style match
                if user.teaching_style_preference and speaker.teaching_style == user.teaching_style_preference:
                    compatible_speakers += 1
                # Check bible approach match
                if user.bible_reading_preference and speaker.bible_approach == user.bible_reading_preference:
                    compatible_speakers += 1
                # Check environment match
                if user.environment_preference and speaker.environment_style == user.environment_preference:
                    compatible_speakers += 1
            
            if church_speakers:
                compatibility_ratio = compatible_speakers / (len(church_speakers) * 3)  # 3 attributes checked
                score += compatibility_ratio * 0.3
        
        # 3. Denomination/environment preference alignment
        if user.environment_preference:
            # Map denominations to likely environment preferences
            denomination_environment_map = {
                'Presbyterian': models.EnvironmentStyle.TRADITIONAL,
                'Catholic': models.EnvironmentStyle.TRADITIONAL,
                'Lutheran': models.EnvironmentStyle.TRADITIONAL,
                'Methodist': models.EnvironmentStyle.BLENDED,
                'Baptist': models.EnvironmentStyle.TRADITIONAL,
                'Non-denominational': models.EnvironmentStyle.CONTEMPORARY,
                'Assembly of God': models.EnvironmentStyle.CONTEMPORARY,
                'Pentecostal': models.EnvironmentStyle.CONTEMPORARY
            }
            
            expected_env = denomination_environment_map.get(church.denomination)
            if expected_env == user.environment_preference:
                score += 0.2
        
        # 4. Church size preference (could be inferred from user behavior)
        # For now, give slight preference to mid-size churches
        if church.membership_count and 200 <= church.membership_count <= 2000:
            score += 0.1
        
        return score
    
    def _get_church_recommendation_reasons(
        self,
        church: models.Church,
        user: models.User,
        liked_speaker_ids: List[int],
        liked_church_ids: List[int],
        db: Session
    ) -> List[str]:
        """Get single-word reasons for church recommendation (for pills)"""
        
        reasons = []
        
        # Check if user liked speakers from this church
        if church.id in liked_church_ids:
            reasons.append("Familiar")
        
        # Check preference alignments
        church_speakers = db.query(models.Speaker).filter(
            models.Speaker.church_id == church.id
        ).all()
        
        if church_speakers:
            for speaker in church_speakers:
                if user.teaching_style_preference and speaker.teaching_style == user.teaching_style_preference:
                    if user.teaching_style_preference.value == "warm_and_conversational":
                        reasons.append("Conversational")
                    elif user.teaching_style_preference.value == "passionate_and_high_energy":
                        reasons.append("Energetic")
                    elif user.teaching_style_preference.value == "calm_and_reflective":
                        reasons.append("Reflective")
                    break
            
            for speaker in church_speakers:
                if user.bible_reading_preference and speaker.bible_approach == user.bible_reading_preference:
                    if user.bible_reading_preference.value == "more_scripture":
                        reasons.append("Scripture-focused")
                    elif user.bible_reading_preference.value == "more_application":
                        reasons.append("Practical")
                    elif user.bible_reading_preference.value == "balanced":
                        reasons.append("Balanced")
                    break
            
            for speaker in church_speakers:
                if user.environment_preference and speaker.environment_style == user.environment_preference:
                    if user.environment_preference.value == "traditional":
                        reasons.append("Traditional")
                    elif user.environment_preference.value == "contemporary":
                        reasons.append("Contemporary")
                    elif user.environment_preference.value == "blended":
                        reasons.append("Blended")
                    break
        
        # Add denomination as a single word
        if church.denomination:
            reasons.append(church.denomination)
        
        # Add size category
        if church.membership_count:
            if church.membership_count < 200:
                reasons.append("Intimate")
            elif church.membership_count <= 2000:
                reasons.append("Mid-size")
            else:
                reasons.append("Large")
        
        return reasons
    
    def get_sermon_recommendations_by_speakers(
        self,
        recommended_speakers: List[Tuple[int, float]],
        db: Session,
        limit: int = 10
    ) -> List[Dict]:
        """Get sermon clips from recommended speakers"""
        
        if not recommended_speakers:
            return []
        
        # Extract speaker IDs and their scores
        speaker_ids = [speaker_id for speaker_id, score in recommended_speakers]
        speaker_scores = {speaker_id: score for speaker_id, score in recommended_speakers}
        
        # Get sermon clips from these speakers
        sermons = db.query(models.Sermon).join(models.Speaker).filter(
            models.Speaker.id.in_(speaker_ids),
            models.Sermon.is_clip == True  # Only clips for recommendations
        ).all()
        
        # Create recommendation objects with scores
        recommendations = []
        for sermon in sermons:
            speaker_score = speaker_scores.get(sermon.speaker_id, 0.0)
            
            recommendation = {
                "sermon_id": sermon.id,
                "title": sermon.title,
                "description": sermon.description,
                "gcs_url": sermon.gcs_url,
                "speaker": {
                    "id": sermon.speaker.id,
                    "name": sermon.speaker.name,
                    "title": sermon.speaker.title,
                    "profile_picture_url": sermon.speaker.profile_picture_url,
                    "teaching_style": sermon.speaker.teaching_style,
                    "bible_approach": sermon.speaker.bible_approach,
                    "environment_style": sermon.speaker.environment_style,
                    "gender": sermon.speaker.gender
                },
                "recommendation_score": speaker_score,
                "matching_reason": "Compatible"
            }
            recommendations.append(recommendation)
        
        # Sort by speaker recommendation score
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return recommendations[:limit]


# Global service instance
ai_service = AIEmbeddingService()


def get_ai_service() -> AIEmbeddingService:
    """Get the global AI embedding service instance"""
    return ai_service


def trigger_ai_recommendation_update(user_id: int, db: Session) -> bool:
    """
    Trigger an AI recommendation update for a user based on their latest sermon preferences.
    This is called automatically when users submit sermon preferences.
    
    Args:
        user_id: The user ID to update recommendations for
        db: Database session
        
    Returns:
        bool: True if recommendations were successfully updated, False otherwise
    """
    try:
        # Get the user
        from app.db import models
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            print(f"⚠️ User {user_id} not found for AI recommendation update")
            return False
        
        # Get AI service
        ai_service = get_ai_service()
        if not ai_service.is_available():
            print(f"⚠️ AI service not available for user {user_id} recommendation update")
            return False
        
        # Get user's selected speakers for context (if any)
        selected_speakers = db.query(models.Speaker).join(models.UserSpeakerPreference).filter(
            models.UserSpeakerPreference.user_id == user_id
        ).all()
        selected_speaker_names = [speaker.name for speaker in selected_speakers]
        
        print(f"🤖 Generating fresh AI recommendations for user {user_id} based on sermon preferences")
        
        # Generate fresh AI recommendations with learning from sermon preferences
        ai_speaker_recs = ai_service.get_ai_recommendations_with_learning(
            user, 
            selected_speaker_names, 
            limit=20,  # Get a good number of recommendations
            force_refresh=True,  # Force fresh generation
            db=db  # Pass database session for learning from ratings
        )
        
        # Store the updated recommendations
        if ai_speaker_recs:
            ai_service.store_ai_recommendations(db, user_id, ai_speaker_recs)
            print(f"✅ Successfully updated AI recommendations for user {user_id} ({len(ai_speaker_recs)} speakers)")
            return True
        else:
            print(f"⚠️ No AI recommendations generated for user {user_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating AI recommendations for user {user_id}: {e}")
        return False
