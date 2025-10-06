from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel_admin import SQLModelAdmin
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
    
    # Add authentication dependency to all routes
    admin_app.dependency_overrides[get_current_user] = get_current_user
    
    # Create SQLModelAdmin instance with authentication
    admin = SQLModelAdmin(engine, admin_app, auth_dependency=get_current_user)
    
    # Register models for admin interface
    admin.add_model(Church, name="Churches", icon="church")
    admin.add_model(Speaker, name="Speakers", icon="user")
    admin.add_model(User, name="Users", icon="users")
    admin.add_model(UserSpeakerPreference, name="User Speaker Preferences", icon="heart")
    admin.add_model(OnboardingQuestion, name="Onboarding Questions", icon="question")
    
    return admin_app

# Create the admin app instance
admin_app = create_admin_app()
