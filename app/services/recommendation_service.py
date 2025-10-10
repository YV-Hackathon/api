"""
ML Recommendation Service

This service integrates with the trained ML model to generate speaker recommendations
and manages the storage/retrieval of recommendations in the database.
"""

import json
import logging
import torch
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.db import models
from app.models.schemas import User
from model.inference_service import get_model_service

# Set up logging
logger = logging.getLogger(__name__)

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
        logger.info(f"Starting recommendation generation - limit: {limit}, model_loaded: {self.model_loaded}")
        logger.debug(f"User preferences: {user_preferences}")
        logger.debug(f"User swipes count: {len(user_swipes) if user_swipes else 0}")
        
        if not self.model_loaded:
            logger.warning("ML model not loaded, using fallback recommendations")
            return self._get_fallback_recommendations(limit, db)
        
        try:
            # This is a simplified version of your query_model.py logic
            device = next(self.model.parameters()).device
            d = self.model.user_embed.embedding_dim
            logger.debug(f"Model device: {device}, embedding_dim: {d}")
            
            # Build preference vector from user traits
            trait_choices = user_preferences.get('trait_choices', [])
            logger.debug(f"Trait choices from preferences: {trait_choices}")
            
            trait_ids = self._traits_to_trait_ids(trait_choices)
            logger.debug(f"Converted trait IDs: {trait_ids}")
            
            p = self._build_preference_vector(trait_ids, device)
            logger.debug(f"Preference vector shape: {p.shape}, norm: {p.norm().item():.4f}")
            
            # Build behavior vector from swipes if available
            u = torch.zeros(d, device=device)
            if user_swipes:
                logger.debug(f"Building behavior vector from {len(user_swipes)} swipes")
                u = self._build_behavior_vector(user_swipes, device)
                logger.debug(f"Behavior vector shape: {u.shape}, norm: {u.norm().item():.4f}")
            else:
                logger.debug("No user swipes provided, using zero behavior vector")
            
            # Blend preferences and behavior
            alpha = 0.4
            q = (1 - alpha) * u + alpha * p
            logger.debug(f"Blended query vector (alpha={alpha}) shape: {q.shape}, norm: {q.norm().item():.4f}")
            
            # Score all candidates
            logger.debug("Starting candidate scoring...")
            candidate_scores = self._score_candidates(q, user_swipes or [], db)
            logger.info(f"Scored {len(candidate_scores)} candidates")
            
            # If no candidates found, fall back to fallback recommendations
            if not candidate_scores:
                logger.warning("No candidates found in ML model, falling back to fallback recommendations")
                return self._get_fallback_recommendations(limit, db)
            
            # Return top K recommendations
            top_k = min(limit, len(candidate_scores))
            final_recommendations = candidate_scores[:top_k]
            logger.info(f"Returning {len(final_recommendations)} recommendations (top {top_k} of {len(candidate_scores)})")
            logger.debug(f"Top recommendations: {final_recommendations[:5]}")  # Log first 5 for debugging
            
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error generating ML recommendations: {e}", exc_info=True)
            return self._get_fallback_recommendations(limit, db)
    
    def _traits_to_trait_ids(self, traits: List[str]) -> List[int]:
        """Convert trait names to trait IDs."""
        if not self.trait2idx:
            logger.warning("trait2idx mapping not available")
            return []
        
        trait_ids = []
        for trait in traits:
            if trait in self.trait2idx:
                trait_ids.append(self.trait2idx[trait])
            else:
                logger.debug(f"Trait '{trait}' not found in trait2idx mapping")
        
        logger.debug(f"Converted {len(traits)} traits to {len(trait_ids)} trait IDs")
        return trait_ids
    
    def _build_preference_vector(self, trait_ids: List[int], device) -> torch.Tensor:
        """Build preference vector from trait IDs."""
        if not trait_ids:
            d = self.model.user_embed.embedding_dim
            logger.debug("No trait IDs provided, returning zero preference vector")
            return torch.zeros(d, device=device)
        
        idx = torch.tensor(trait_ids, dtype=torch.long, device=device)
        emb = self.model.trait_bag.weight.index_select(0, idx)
        result = emb.mean(dim=0)
        logger.debug(f"Built preference vector from {len(trait_ids)} traits, shape: {result.shape}")
        return result
    
    def _build_behavior_vector(self, user_swipes: List[Dict], device) -> torch.Tensor:
        """Build behavior vector from user swipes/ratings."""
        d = self.model.user_embed.embedding_dim
        liked_vs, disliked_vs = [], []
        skipped_swipes = 0
        
        logger.debug(f"Processing {len(user_swipes)} swipes for behavior vector")
        
        for swipe in user_swipes:
            speaker_id = int(swipe.get('speaker_id', 0))
            rating = float(swipe.get('rating', 0))
            
            if speaker_id not in self.pastor2idx:
                skipped_swipes += 1
                logger.debug(f"Skipping swipe for speaker_id {speaker_id} (not in pastor2idx)")
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
        
        logger.debug(f"Processed swipes: {len(liked_vs)} liked, {len(disliked_vs)} disliked, {skipped_swipes} skipped")
        
        v_like = torch.stack(liked_vs, dim=0).mean(0) if liked_vs else torch.zeros(d, device=device)
        v_dis = torch.stack(disliked_vs, dim=0).mean(0) if disliked_vs else torch.zeros(d, device=device)
        
        result = v_like - 0.5 * v_dis
        logger.debug(f"Behavior vector shape: {result.shape}, norm: {result.norm().item():.4f}")
        return result
    
    def _score_candidates(self, query_vector: torch.Tensor, user_swipes: List[Dict], db: Session = None) -> List[Tuple[int, float]]:
        """Score all candidate speakers against the query vector."""
        device = query_vector.device
        logger.debug(f"Scoring candidates on device: {device}")
        
        # Get already-swiped speaker IDs
        swiped_ids = {int(s.get('speaker_id', 0)) for s in user_swipes}
        logger.debug(f"Swiped speaker IDs: {swiped_ids}")
        
        # Get speakers with sermons if DB session provided
        speakers_with_sermons = set()
        if db:
            from app.db import models
            speakers_with_sermons_query = db.query(models.Speaker.id).join(models.Sermon).distinct()
            speakers_with_sermons = {speaker.id for speaker in speakers_with_sermons_query.all()}
            logger.info(f"Found {len(speakers_with_sermons)} speakers with sermons in database")
        
        # Get candidate indices (exclude already swiped and speakers without sermons)
        cand_idxs = []
        excluded_swiped = 0
        excluded_no_sermons = 0
        
        for speaker_id, idx in self.pastor2idx.items():
            if speaker_id in swiped_ids:
                excluded_swiped += 1
                continue
            if db and speakers_with_sermons and speaker_id not in speakers_with_sermons:
                excluded_no_sermons += 1
                continue
            cand_idxs.append(idx)
        
        logger.info(f"Found {len(cand_idxs)} candidate speakers out of {len(self.pastor2idx)} total speakers in model")
        logger.debug(f"Excluded {excluded_swiped} already swiped speakers, {excluded_no_sermons} speakers without sermons")
        
        if not cand_idxs:
            logger.warning("No candidate speakers found - all speakers either swiped or don't have sermons")
            return []
        
        cand_idx_t = torch.tensor(cand_idxs, dtype=torch.long, device=device)
        logger.debug(f"Created candidate tensor with shape: {cand_idx_t.shape}")
        
        # Build trait bags for all candidates
        flat, offsets, total = [], [0], 0
        for i in cand_idxs:
            f = self.pastor_trait_ids[i].tolist()
            flat.extend(f)
            total += len(f)
            offsets.append(total)
        
        flat_t = torch.tensor(flat, dtype=torch.long, device=device)
        offsets_t = torch.tensor(offsets[:-1], dtype=torch.long, device=device)
        logger.debug(f"Built trait bags: {len(flat)} total traits, {len(offsets)-1} candidates")
        
        # Calculate item vectors
        v_id = self.model.pastor_id_emb(cand_idx_t)
        v_feat = self.model.trait_bag(flat_t, offsets_t)
        V = v_id + v_feat
        logger.debug(f"Item vectors shape: {V.shape}")
        
        # Calculate scores
        dot = (V * query_vector.unsqueeze(0)).sum(-1) / self.model._scale
        bias = self.model.global_bias + self.model.pastor_bias(cand_idx_t).squeeze(-1)
        scores = (dot + bias).detach().cpu()
        logger.debug(f"Score statistics - min: {scores.min().item():.4f}, max: {scores.max().item():.4f}, mean: {scores.mean().item():.4f}")
        
        # Convert to (speaker_id, score) tuples and sort
        idx2speaker_id = {v: k for k, v in self.pastor2idx.items()}
        results = [(int(idx2speaker_id[cand_idxs[i]]), float(scores[i])) 
                   for i in range(len(cand_idxs))]
        
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        logger.debug(f"Top 3 scores: {sorted_results[:3]}")
        return sorted_results
    
    def _get_fallback_recommendations(self, limit: int, db: Session = None) -> List[Tuple[int, float]]:
        """Generate fallback recommendations when ML model is not available."""
        logger.info(f"Generating fallback recommendations with limit: {limit}")
        
        if db:
            # Get speakers with sermons for realistic fallback
            from app.db import models
            speakers_with_sermons = db.query(models.Speaker.id).join(models.Sermon).filter(
                models.Speaker.is_recommended == True
            ).distinct().limit(limit).all()
            
            logger.debug(f"Found {len(speakers_with_sermons)} recommended speakers with sermons")
            
            fallback_recs = []
            for i, speaker in enumerate(speakers_with_sermons):
                # Assign decreasing scores
                score = 0.95 - (i * 0.05)
                fallback_recs.append((speaker.id, max(score, 0.5)))
            
            logger.info(f"Generated {len(fallback_recs)} fallback recommendations with sermons")
            return fallback_recs
        else:
            # Return mock recommendations - in production, you might want to use simple heuristics
            # based on speaker popularity, user preferences, etc.
            mock_recommendations = [
                (1, 0.95), (2, 0.92), (3, 0.89), (4, 0.87), (5, 0.85),
                (6, 0.83), (7, 0.81), (8, 0.79), (9, 0.77), (10, 0.75)
            ]
            logger.info(f"Using mock recommendations (limit: {limit})")
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
    logger.info(f"Triggering recommendation update for user {user_id}")
    
    try:
        # Get the user
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found for recommendation update")
            return False
        
        logger.debug(f"Found user: {user.email if hasattr(user, 'email') else 'unknown'}")
        
        # Get user's sermon preferences to build user_swipes data
        sermon_preferences = db.query(models.UserSermonPreference).filter(
            models.UserSermonPreference.user_id == user_id
        ).all()
        
        logger.debug(f"Found {len(sermon_preferences)} sermon preferences for user {user_id}")
        
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
        
        logger.info(f"Updating recommendations for user {user_id} based on {len(user_swipes)} sermon preferences")
        
        # Build user preferences from profile
        user_preferences = {
            'trait_choices': [],  # Could be populated from user traits if available
            'teaching_style': user.teaching_style_preference,
            'bible_approach': user.bible_reading_preference,
            'environment_style': user.environment_preference,
            'gender_preference': user.gender_preference
        }
        
        logger.debug(f"User preferences: {user_preferences}")

        JSON_INPUT = {
            "trait_choices": [
                "Gender::Female pastor",
                "Preaching method::Topical",
                "Theological tradition::Mixed",
                "Women in leadership::Egalitarian",
            ],
            "swipes": [
                {"pastorName": "AndyStanley,", "pastorId": 44, "rating": 5},
                {"pastorName": "RickWarren", "pastorId": 45, "rating": 4},
                {"pastorName": "JohnPiper", "pastorId": 48, "rating": 2},
            ],
        }

        user_preferences = {"trait_choices": JSON_INPUT.get("trait_choices", [])}
        user_swipes = [{"speaker_id": s.get("pastorId"), "rating": float(s.get("rating", 0))} for s in JSON_INPUT.get("swipes", [])]
        ml_service = get_model_service()
        speaker_recs = ml_service.generate_recommendations(
            user_preferences=user_preferences,
            user_swipes=user_swipes,
            limit=20
        )
        
        # Store the updated recommendations
        if speaker_recs:
            stored_recs = ml_service.store_recommendations(db, user_id, speaker_recs)
            logger.info(f"Successfully updated recommendations for user {user_id} - stored {len(speaker_recs)} recommendations")
            return True
        else:
            logger.warning(f"No recommendations generated for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating recommendations for user {user_id}: {e}", exc_info=True)
        return False
