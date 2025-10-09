from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_v1.api import api_router
from app.db.database import engine
from app.db import models
from app.admin import admin_app

# Note: Database tables are now managed by Alembic migrations
# Run 'alembic upgrade head' to apply migrations

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PewPal API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    redirect_slashes=True
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount admin interface
app.mount("/admin", admin_app)

@app.get("/")
async def root():
    return {"message": "PewPal API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
