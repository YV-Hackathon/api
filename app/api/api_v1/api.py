from fastapi import APIRouter
from app.api.api_v1.endpoints import churches, speakers, users, onboarding, sermons, church_followers

api_router = APIRouter()

api_router.include_router(churches.router, prefix="/churches", tags=["churches"])
api_router.include_router(speakers.router, prefix="/speakers", tags=["speakers"])
api_router.include_router(sermons.router, prefix="/sermons", tags=["sermons"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(church_followers.router, prefix="/church-followers", tags=["church-followers"])
