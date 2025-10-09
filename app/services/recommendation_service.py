"""
ML Recommendation Service

This service integrates with the trained ML model to generate speaker recommendations
and manages the storage/retrieval of recommendations in the database.
"""

import json
import torch
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.db import models
from app.models.schemas import User

# Import your model utilities
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'model'))

try:
    from utils.save_or_load import load_artifacts
    from utils.model import build_mappings
    import pandas as pd
except ImportError:
    # Fallback for development/testing when model artifacts aren't available
    print("Warning: ML model utilities not available. Using mock recommendations.")


class MLRecommendationService:
    """Service for generating and managing ML-based speaker recommendations."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the ML recommendation service.
        
        Args:
            model_path: Path to the trained model artifacts. If None, uses default path.
        """
        self.model = None
        self.user_enc = None
        self.pastor_enc = None
        self.pastor_trait_ids = None
        self.pastor2idx = None
        self.trait2idx = None
        self.model_loaded = False
        
        if model_path is None:
            model_path = Path(__file__).parent.parent.parent / "model" / "artifacts" / "model_1759812063"
        
        self._load_model(model_path)
    
    def _load_model(self, model_path: Path) -> None:
        """Load the trained ML model and associated artifacts."""
        try:
            # Load model artifacts
            self.model, self.user_enc, self.pastor_enc, self.pastor_trait_ids, _, _ = load_artifacts(model_path)
            
            # Load data to rebuild mappings
            ratings_path = Path(__file__).parent.parent.parent / "model" / "data" / "pastor_ratings.csv"
            pastor_path = Path(__file__).parent.parent.parent / "model" / "data" / "pastor_traits.csv"
            
            if ratings_path.exists() and pastor_path.exists():
                rating_df = pd.read_csv(ratings_path)
                pastor_df = pd.read_csv(pastor_path)
                
                # Rebuild mappings
                user2idx, self.pastor2idx, self.trait2idx, _ = build_mappings(rating_df, pastor_df)
                
                self.model_loaded = True
                print("✅ ML model loaded successfully")
            else:
                print("⚠️ Model data files not found, using fallback recommendations")
                
        except Exception as e:
            print(f"⚠️ Failed to load ML model: {e}")
            print("Using fallback recommendations")
    
    def generate_recommendations(
        self, 
        user_preferences: Dict, 
        user_swipes: List[Dict] = None,
        limit: int = 10,
        db: Session = None
    ) -> List[Tuple[int, float]]:
        """Generate speaker recommendations for a user.
        
        Args:
            user_preferences: Dictionary containing user's trait preferences
            user_swipes: List of user's previous swipes/ratings (optional)
            limit: Maximum number of recommendations to return
            db: Database session to filter speakers with sermons
            
        Returns:
            List of tuples (speaker_id, confidence_score)
        """
        if not self.model_loaded:
            return self._get_fallback_recommendations(limit, db)
        
        try:
            # This is a simplified version of your query_model.py logic
            device = next(self.model.parameters()).device
            d = self.model.user_embed.embedding_dim
            
            # Build preference vector from user traits
            trait_choices = user_preferences.get('trait_choices', [])
            trait_ids = self._traits_to_trait_ids(trait_choices)
            p = self._build_preference_vector(trait_ids, device)
            
            # Build behavior vector from swipes if available
            u = torch.zeros(d, device=device)
            if user_swipes:
                u = self._build_behavior_vector(user_swipes, device)
            
            # Blend preferences and behavior
            alpha = 0.4
            q = (1 - alpha) * u + alpha * p
            
            # Score all candidates
            candidate_scores = self._score_candidates(q, user_swipes or [], db)
            
            # Return top K recommendations
            top_k = min(limit, len(candidate_scores))
            return candidate_scores[:top_k]
            
        except Exception as e:
            print(f"Error generating ML recommendations: {e}")
            return self._get_fallback_recommendations(limit, db)
    
    def _traits_to_trait_ids(self, traits: List[str]) -> List[int]:
        """Convert trait names to trait IDs."""
        if not self.trait2idx:
            return []
        
        trait_ids = []
        for trait in traits:
            if trait in self.trait2idx:
                trait_ids.append(self.trait2idx[trait])
        return trait_ids
    
    def _build_preference_vector(self, trait_ids: List[int], device) -> torch.Tensor:
        """Build preference vector from trait IDs."""
        if not trait_ids:
            d = self.model.user_embed.embedding_dim
            return torch.zeros(d, device=device)
        
        idx = torch.tensor(trait_ids, dtype=torch.long, device=device)
        emb = self.model.trait_bag.weight.index_select(0, idx)
        return emb.mean(dim=0)
    
    def _build_behavior_vector(self, user_swipes: List[Dict], device) -> torch.Tensor:
        """Build behavior vector from user swipes/ratings."""
        d = self.model.user_embed.embedding_dim
        liked_vs, disliked_vs = [], []
        
        for swipe in user_swipes:
            speaker_id = int(swipe.get('speaker_id', 0))
            rating = float(swipe.get('rating', 0))
            
            if speaker_id not in self.pastor2idx:
                continue
                
            idx = self.pastor2idx[speaker_id]
            v_id = self.model.pastor_id_emb.weight[idx]
            f_ids = self.pastor_trait_ids[idx].to(device)
            v_feat = self.model.trait_bag.weight[f_ids].mean(0)
            v = v_id + v_feat
            
            if rating >= 4.0:
                liked_vs.append(v)
            else:
                disliked_vs.append(v)
        
        v_like = torch.stack(liked_vs, dim=0).mean(0) if liked_vs else torch.zeros(d, device=device)
        v_dis = torch.stack(disliked_vs, dim=0).mean(0) if disliked_vs else torch.zeros(d, device=device)
        
        return v_like - 0.5 * v_dis
    
    def _score_candidates(self, query_vector: torch.Tensor, user_swipes: List[Dict], db: Session = None) -> List[Tuple[int, float]]:
        """Score all candidate speakers against the query vector."""
        device = query_vector.device
        
        # Get already-swiped speaker IDs
        swiped_ids = {int(s.get('speaker_id', 0)) for s in user_swipes}
        
        # Get speakers with sermons if DB session provided
        speakers_with_sermons = set()
        if db:
            from app.db import models
            speakers_with_sermons_query = db.query(models.Speaker.id).join(models.Sermon).distinct()
            speakers_with_sermons = {speaker.id for speaker in speakers_with_sermons_query.all()}
            print(f"🎯 ML: Found {len(speakers_with_sermons)} speakers with sermons")
        
        # Get candidate indices (exclude already swiped and speakers without sermons)
        cand_idxs = []
        for speaker_id, idx in self.pastor2idx.items():
            if speaker_id in swiped_ids:
                continue
            if db and speakers_with_sermons and speaker_id not in speakers_with_sermons:
                continue
            cand_idxs.append(idx)
        
        if not cand_idxs:
            return []
        
        cand_idx_t = torch.tensor(cand_idxs, dtype=torch.long, device=device)
        
        # Build trait bags for all candidates
        flat, offsets, total = [], [0], 0
        for i in cand_idxs:
            f = self.pastor_trait_ids[i].tolist()
            flat.extend(f)
            total += len(f)
            offsets.append(total)
        
        flat_t = torch.tensor(flat, dtype=torch.long, device=device)
        offsets_t = torch.tensor(offsets[:-1], dtype=torch.long, device=device)
        
        # Calculate item vectors
        v_id = self.model.pastor_id_emb(cand_idx_t)
        v_feat = self.model.trait_bag(flat_t, offsets_t)
        V = v_id + v_feat
        
        # Calculate scores
        dot = (V * query_vector.unsqueeze(0)).sum(-1) / self.model._scale
        bias = self.model.global_bias + self.model.pastor_bias(cand_idx_t).squeeze(-1)
        scores = (dot + bias).detach().cpu()
        
        # Convert to (speaker_id, score) tuples and sort
        idx2speaker_id = {v: k for k, v in self.pastor2idx.items()}
        results = [(int(idx2speaker_id[cand_idxs[i]]), float(scores[i])) 
                   for i in range(len(cand_idxs))]
        
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def _get_fallback_recommendations(self, limit: int, db: Session = None) -> List[Tuple[int, float]]:
        """Generate fallback recommendations when ML model is not available."""
        if db:
            # Get speakers with sermons for realistic fallback
            from app.db import models
            speakers_with_sermons = db.query(models.Speaker.id).join(models.Sermon).filter(
                models.Speaker.is_recommended == True
            ).distinct().limit(limit).all()
            
            fallback_recs = []
            for i, speaker in enumerate(speakers_with_sermons):
                # Assign decreasing scores
                score = 0.95 - (i * 0.05)
                fallback_recs.append((speaker.id, max(score, 0.5)))
            
            print(f"🔄 Generated {len(fallback_recs)} fallback recommendations with sermons")
            return fallback_recs
        else:
            # Return mock recommendations - in production, you might want to use simple heuristics
            # based on speaker popularity, user preferences, etc.
            mock_recommendations = [
                (1, 0.95), (2, 0.92), (3, 0.89), (4, 0.87), (5, 0.85),
                (6, 0.83), (7, 0.81), (8, 0.79), (9, 0.77), (10, 0.75)
            ]
            return mock_recommendations[:limit]
    
    def store_recommendations(
        self, 
        db: Session, 
        user_id: int, 
        speaker_recommendations: List[Tuple[int, float]]
    ) -> models.Recommendations:
        """Store speaker recommendations in the database.
        
        Args:
            db: Database session
            user_id: User ID
            speaker_recommendations: List of (speaker_id, score) tuples
            
        Returns:
            The stored Recommendations object
        """
        speaker_ids = [int(rec[0]) for rec in speaker_recommendations]
        scores = [float(rec[1]) for rec in speaker_recommendations]
        
        # Check if recommendations already exist for this user
        existing = db.query(models.Recommendations).filter(
            models.Recommendations.user_id == user_id
        ).first()
        
        if existing:
            # Update existing recommendations
            existing.speaker_ids = speaker_ids
            existing.scores = scores
            db.commit()
            db.refresh(existing)
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
            return new_recommendations
    
    def get_stored_recommendations(
        self, 
        db: Session, 
        user_id: int
    ) -> Optional[models.Recommendations]:
        """Retrieve stored recommendations for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Recommendations object or None if not found
        """
        return db.query(models.Recommendations).filter(
            models.Recommendations.user_id == user_id
        ).first()


# Global service instance
ml_service = MLRecommendationService()


def get_ml_service() -> MLRecommendationService:
    """Get the global ML recommendation service instance."""
    return ml_service


def trigger_recommendation_update(user_id: int, db: Session) -> bool:
    """
    Trigger a recommendation update for a user based on their latest sermon preferences.
    This is called automatically when users submit sermon preferences.
    
    Args:
        user_id: The user ID to update recommendations for
        db: Database session
        
    Returns:
        bool: True if recommendations were successfully updated, False otherwise
    """
    try:
        # Get the user
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            print(f"⚠️ User {user_id} not found for recommendation update")
            return False
        
        # Get user's sermon preferences to build user_swipes data
        sermon_preferences = db.query(models.UserSermonPreference).filter(
            models.UserSermonPreference.user_id == user_id
        ).all()
        
        # Convert sermon preferences to swipes format for ML model
        user_swipes = []
        for pref in sermon_preferences:
            # Get the sermon to access speaker_id
            sermon = db.query(models.Sermon).filter(models.Sermon.id == pref.sermon_id).first()
            if sermon:
                # Convert thumbs_up/thumbs_down to numerical rating
                rating = 5.0 if pref.preference == 'thumbs_up' else 2.0
                user_swipes.append({
                    'speaker_id': sermon.speaker_id,
                    'rating': rating,
                    'sermon_id': pref.sermon_id
                })
        
        print(f"🔄 Updating recommendations for user {user_id} based on {len(user_swipes)} sermon preferences")
        
        # Build user preferences from profile
        user_preferences = {
            'trait_choices': [],  # Could be populated from user traits if available
            'teaching_style': user.teaching_style_preference,
            'bible_approach': user.bible_reading_preference,
            'environment_style': user.environment_preference,
            'gender_preference': user.gender_preference
        }
        
        # Generate new recommendations using ML model with user swipes
        ml_service = get_ml_service()
        speaker_recs = ml_service.generate_recommendations(
            user_preferences=user_preferences,
            user_swipes=user_swipes,
            limit=20,
            db=db
        )
        
        # Store the updated recommendations
        if speaker_recs:
            stored_recs = ml_service.store_recommendations(db, user_id, speaker_recs)
            print(f"✅ Successfully updated recommendations for user {user_id}")
            return True
        else:
            print(f"⚠️ No recommendations generated for user {user_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating recommendations for user {user_id}: {e}")
        return False
