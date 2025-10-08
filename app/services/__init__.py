"""Services package for business logic and external integrations."""

from .recommendation_service import MLRecommendationService, get_ml_service

__all__ = ['MLRecommendationService', 'get_ml_service']
