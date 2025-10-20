from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import torch
import pandas as pd
import torch.nn.functional as F

from utils.save_or_load import load_artifacts
from utils.model import build_mappings

from ..app.models import schemas as models

from sqlalchemy.orm import Session

# ---- Trait validation utilities (aligned with query_model) ----
import re
import unicodedata


def _normalize_text(s: str) -> str:
    s = unicodedata.normalize('NFKC', s)
    s = s.replace('\u2013', '-').replace('\u2014', '-')
    s = s.replace('\n', ' ').replace('\r', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# Value-only canonical triples for validation (no group prefixes necessary here)
CANONICAL_TRIPLES = {
    (
        "Practical, everyday life application",
        "Deep, verse-by-verse Scripture teaching",
        "A balance of both",
    ),
    (
        "Warm and conversational",
        "Calm and reflective",
        "Passionate and high-energy",
    ),
    ("Traditional", "Contemporary", "Blended"),
    ("Male pastor", "Female pastor", "No preference"),
    ("Expository", "Topical", "Blend"),
    ("Reformed/Calvinist", "Arminian/Wesleyan", "Mixed"),
    ("Continuationist", "Cessationist", "Open-but-cautious"),
    ("High-church", "Mid-liturgical", "Low-church"),
    ("Short (<25m)", "Medium (25–40m)", "Long (>40m)"),
    ("Weekly altar call", "Occasional", "Rare/none"),
    ("Weekly", "Monthly/Quarterly", "Occasional"),
    (
        "Episcopal (bishops)",
        "Presbyterian (elders)",
        "Congregational (local autonomy)",
    ),
    ("Egalitarian", "Complementarian", "Mixed/transitioning"),
    ("Small (<200)", "Mid (200–1000)", "Mega/Multisite (2000+)"),
    ("Small-groups centric", "Classes/courses", "From-the-pulpit"),
    ("Seeker-sensitive", "Church-family-oriented", "Hybrid"),
    ("Call-and-response", "Steady monologue", "Contemplative"),
}

TRAIT_LIST = {_normalize_text(t) for triple in CANONICAL_TRIPLES for t in triple}


def _validate_trait_values(traits: List[str]) -> None:
    if not traits:
        return
    normalized = {_normalize_text(t.split("::", 1)[-1]) for t in traits}
    if not normalized.issubset(TRAIT_LIST):
        bad = sorted([t for t in traits if _normalize_text(t.split("::", 1)[-1]) not in TRAIT_LIST])
        raise ValueError(f"Unknown trait(s): {bad}")


class ModelInferenceService:
    """Loads model artifacts and exposes inference utilities.

    Mirrors query_model scoring and explanation behavior, including readable
    trait alignment (topItemTraitsByAlignment) derived from trait embeddings.
    """

    def __init__(self) -> None:
        self.model = None
        self.user_enc = None
        self.pastor_enc = None
        self.pastor_trait_ids = None  # list[LongTensor] indexed by internal pastor idx
        self.pastor2idx: Optional[Dict[int, int]] = None
        self.trait2idx: Optional[Dict[str, int]] = None
        self.model_loaded: bool = False

        base_dir = Path(__file__).parent
        # Update to your preferred artifact directory
        self.model_path = Path(base_dir / "artifacts", "model_1760050628")

        self._load_model(Path(self.model_path))

    def _load_model(self, model_path: Path) -> None:
        try:
            self.model, self.user_enc, self.pastor_enc, self.pastor_trait_ids, _, _ = load_artifacts(self.model_path)

            # Rebuild mappings using the same sources used in training/querying
            data_dir = Path(__file__).parent / "data"
            ratings_path = (data_dir / "user_ratings.csv").resolve()
            pastor_path = (data_dir / "pastor_traits_mapped.csv").resolve()

            if ratings_path.exists() and pastor_path.exists():
                rating_df = pd.read_csv(ratings_path)
                pastor_df = pd.read_csv(pastor_path)
                _, self.pastor2idx, self.trait2idx, _ = build_mappings(rating_df, pastor_df)
                self.model_loaded = True
                print(f"✅ Model loaded from {self.model_path}")
            else:
                print("⚠️ Data files not found for mappings; inference limited")
        except Exception as e:
            print(f"⚠️ Failed to load model artifacts from {self.model_path}: {e}")
            self.model_loaded = False

    # ---------- Public API ----------
    def generate_recommendations(
        self,
        user_preferences: Dict,
        user_swipes: Optional[List[Dict]] = None,
        limit: int = 10,
        exclude_speaker_ids: Optional[Iterable[int]] = None,
        allowed_speaker_ids: Optional[Iterable[int]] = None,
    ) -> List[Tuple[int, float]]:
        """Return a ranked list of (speaker_id, score)."""
        if not self.model_loaded:
            return []

        try:
            device = next(self.model.parameters()).device
            d = self.model.user_embed.embedding_dim

            trait_choices = user_preferences.get("trait_choices", [])
            _validate_trait_values(trait_choices)
            trait_ids = self._traits_to_trait_ids(trait_choices)
            p = self._build_preference_vector(trait_ids, device)

            u = torch.zeros(d, device=device)
            if user_swipes:
                u = self._build_behavior_vector(user_swipes, device)

            alpha = 0.4
            q = (1 - alpha) * u + alpha * p

            candidate_scores = self._score_candidates(
                q,
                user_swipes or [],
                exclude_speaker_ids=exclude_speaker_ids,
                allowed_speaker_ids=allowed_speaker_ids,
            )

            top_k = min(limit, len(candidate_scores))
            return candidate_scores[:top_k]
        except Exception as e:
            print(f"Error during inference: {e}")
            return []

    def generate_recommendations_detailed(
        self,
        user_preferences: Dict,
        user_swipes: Optional[List[Dict]] = None,
        limit: int = 10,
        exclude_speaker_ids: Optional[Iterable[int]] = None,
        allowed_speaker_ids: Optional[Iterable[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Return recommendations with top trait alignment explanations.

        Fields per item: speaker_id, score, content_cosine, topItemTraitsByAlignment.
        """
        if not self.model_loaded:
            return []

        try:
            device = next(self.model.parameters()).device
            d = self.model.user_embed.embedding_dim

            trait_choices = user_preferences.get("trait_choices", [])
            _validate_trait_values(trait_choices)
            trait_ids = self._traits_to_trait_ids(trait_choices)
            p = self._build_preference_vector(trait_ids, device)

            u = torch.zeros(d, device=device)
            if user_swipes:
                u = self._build_behavior_vector(user_swipes, device)

            alpha = 0.4
            q = (1 - alpha) * u + alpha * p

            results = self._score_candidates(
                q,
                user_swipes or [],
                exclude_speaker_ids=exclude_speaker_ids,
                allowed_speaker_ids=allowed_speaker_ids,
            )

            top_k = results[: min(limit, len(results))]
            # Mirror query_model: map trait ids back to readable tokens
            idx2trait = {v: k for k, v in (self.trait2idx or {}).items()}
            detailed: List[Dict[str, Any]] = []
            for speaker_id, score in top_k:
                internal_idx = None
                if self.pastor2idx and speaker_id in self.pastor2idx:
                    internal_idx = self.pastor2idx[speaker_id]
                if internal_idx is None:
                    continue

                f_ids = self.pastor_trait_ids[internal_idx].to(device)
                v_feat = self.model.trait_bag.weight[f_ids].mean(0)
                content_cosine = float(F.cosine_similarity(p.unsqueeze(0), v_feat.unsqueeze(0), dim=1).item())

                trait_align: List[Tuple[str, float]] = []
                for fid in f_ids.tolist():
                    token = idx2trait.get(fid, f"fid:{fid}")
                    align_score = float(torch.dot(p, self.model.trait_bag.weight[fid]).item())
                    trait_align.append((token, align_score))
                trait_align.sort(key=lambda x: x[1], reverse=True)
                top_trait_explanations = [t for t, _ in trait_align[:3]]

                detailed.append({
                    "speaker_id": int(speaker_id),
                    "score": float(score),
                    "content_cosine": content_cosine,
                    "topItemTraitsByAlignment": top_trait_explanations,
                    "topItemTraits": top_trait_explanations,  # alias if desired
                })

            return detailed
        except Exception as e:
            print(f"Error during detailed inference: {e}")
            return []

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
    # ---------- Internal helpers ----------
    def _traits_to_trait_ids(self, traits: List[str]) -> List[int]:
        """Resolve trait selections to trained IDs when training used value-only tokens.

        - Accepts inputs like "Group::Value" or just "Value".
        - Always looks up by the Value portion against self.trait2idx keys.
        - Performs lenient matching (ignoring commas) when exact value isn't found.
        """
        if not self.trait2idx:
            return []

        def norm(s: str) -> str:
            return ' '.join(str(s).replace('–', '-').split()).strip()

        def loose_norm(s: str) -> str:
            return norm(s).replace(',', '')

        exact_value_to_key: Dict[str, str] = {}
        loose_value_to_keys: Dict[str, List[str]] = {}

        for tok in self.trait2idx.keys():
            value_part = tok.split('::', 1)[-1]
            v_exact = norm(value_part)
            v_loose = loose_norm(value_part)
            exact_value_to_key.setdefault(v_exact, tok)
            loose_value_to_keys.setdefault(v_loose, []).append(tok)

        resolved_keys: List[str] = []
        for raw in traits:
            value_only = raw.split('::', 1)[-1]
            v_exact = norm(value_only)
            v_loose = loose_norm(value_only)

            key = exact_value_to_key.get(v_exact)
            if key is None:
                candidates = loose_value_to_keys.get(v_loose, [])
                if not candidates:
                    raise KeyError(f"Unknown trait value: {raw}")
                key = candidates[0]
            resolved_keys.append(key)

        return [self.trait2idx[k] for k in resolved_keys]

    def _build_preference_vector(self, trait_ids: List[int], device) -> torch.Tensor:
        if not trait_ids:
            d = self.model.user_embed.embedding_dim
            return torch.zeros(d, device=device)
        idx = torch.tensor(trait_ids, dtype=torch.long, device=device)
        emb = self.model.trait_bag.weight.index_select(0, idx)
        return emb.mean(dim=0)

    def _build_behavior_vector(self, user_swipes: List[Dict], device) -> torch.Tensor:
        d = self.model.user_embed.embedding_dim
        liked_vs: List[torch.Tensor] = []
        disliked_vs: List[torch.Tensor] = []

        for swipe in user_swipes:
            speaker_id = int(swipe.get("speaker_id", 0))
            rating = float(swipe.get("rating", 0))

            if not self.pastor2idx or speaker_id not in self.pastor2idx:
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

    def _score_candidates(
        self,
        query_vector: torch.Tensor,
        user_swipes: List[Dict],
        exclude_speaker_ids: Optional[Iterable[int]] = None,
        allowed_speaker_ids: Optional[Iterable[int]] = None,
    ) -> List[Tuple[int, float]]:
        device = query_vector.device

        swiped_ids = {int(s.get("speaker_id", 0)) for s in user_swipes}
        exclude = set(exclude_speaker_ids or []) | swiped_ids
        allow = set(allowed_speaker_ids or [])

        if not self.pastor2idx:
            return []

        cand_idxs: List[int] = []
        cand_speaker_ids: List[int] = []
        for speaker_id, idx in self.pastor2idx.items():
            if speaker_id in exclude:
                continue
            if allow and speaker_id not in allow:
                continue
            cand_idxs.append(idx)
            cand_speaker_ids.append(speaker_id)

        if not cand_idxs:
            return []

        cand_idx_t = torch.tensor(cand_idxs, dtype=torch.long, device=device)

        flat: List[int] = []
        offsets: List[int] = [0]
        total = 0
        for i in cand_idxs:
            f = self.pastor_trait_ids[i].tolist()
            flat.extend(f)
            total += len(f)
            offsets.append(total)

        flat_t = torch.tensor(flat, dtype=torch.long, device=device)
        offsets_t = torch.tensor(offsets[:-1], dtype=torch.long, device=device)

        v_id = self.model.pastor_id_emb(cand_idx_t)
        v_feat = self.model.trait_bag(flat_t, offsets_t)
        V = v_id + v_feat

        dot = (V * query_vector.unsqueeze(0)).sum(-1) / self.model._scale
        bias = self.model.global_bias + self.model.pastor_bias(cand_idx_t).squeeze(-1)
        scores = (dot + bias).detach().cpu()

        results = [(int(cand_speaker_ids[i]), float(scores[i])) for i in range(len(cand_speaker_ids))]
        return sorted(results, key=lambda x: x[1], reverse=True)


# Global singleton instance
_global_service: Optional[ModelInferenceService] = None


def get_model_service() -> ModelInferenceService:
    global _global_service
    if _global_service is None:
        _global_service = ModelInferenceService()
    return _global_service


