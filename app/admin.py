from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqladmin import Admin, BaseView
from sqlalchemy import create_engine
from app.db.database import engine
from app.db.models import Church, Speaker, User, UserSpeakerPreference, OnboardingQuestion
from app.core.config import settings
import secrets

# Simple authentication
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Simple username/password authentication for admin access."""
    # You can change these credentials or load from environment variables
    correct_username = "admin"
    correct_password = "admin123"  # Change this to a secure password!
    
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def create_admin_app() -> FastAPI:
    """Create a FastAPI admin interface for database management."""
    
    admin_app = FastAPI(
        title="Database Admin Panel",
        description="Admin interface for managing database records",
        version="1.0.0"
    )
    
    # Create SQLAdmin instance
    admin = Admin(admin_app, engine, authentication_backend=get_current_user)
    
    # Register models for admin interface
    admin.add_view(Church)
    admin.add_view(Speaker)
    admin.add_view(User)
    admin.add_view(UserSpeakerPreference)
    admin.add_view(OnboardingQuestion)
    
    return admin_app

# Create the admin app instance
admin_app = create_admin_app()
