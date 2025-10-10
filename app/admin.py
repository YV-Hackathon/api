from fastapi import FastAPI
from sqladmin import Admin, ModelView
from app.db.database import engine
from app.db.models import Church, Speaker, User, UserSpeakerPreference, OnboardingQuestion, Sermon, UserSermonPreference, FeaturedSermon

def create_admin_app() -> FastAPI:
    """Create a FastAPI admin interface for database management."""
    
    admin_app = FastAPI(
        title="Database Admin Panel",
        description="Admin interface for managing database records",
        version="1.0.0"
    )
    
    # Create SQLAdmin instance (no authentication for now)
    # Set base_url to "/" so it mounts at the root of the admin app
    admin = Admin(admin_app, engine, base_url="/")
    
    # Create ModelView classes for each model
    class ChurchAdmin(ModelView, model=Church):
        icon = "fa-solid fa-church"
        column_list = [Church.id, Church.name, Church.denomination, Church.email, Church.phone, Church.is_active]
        column_searchable_list = [Church.name, Church.denomination, Church.email]
        column_sortable_list = [Church.id, Church.name, Church.created_at]
    
    class SpeakerAdmin(ModelView, model=Speaker):
        icon = "fa-solid fa-microphone"
        column_list = [Speaker.id, Speaker.name, Speaker.title, Speaker.email, Speaker.phone, Speaker.is_recommended]
        column_searchable_list = [Speaker.name, Speaker.title, Speaker.email]
        column_sortable_list = [Speaker.id, Speaker.name, Speaker.created_at]
    
    class UserAdmin(ModelView, model=User):
        icon = "fa-solid fa-users"
        column_list = [User.id, User.username, User.email, User.first_name, User.last_name, User.is_active]
        column_searchable_list = [User.username, User.email, User.first_name, User.last_name]
        column_sortable_list = [User.id, User.username, User.created_at]
    
    class UserSpeakerPreferenceAdmin(ModelView, model=UserSpeakerPreference):
        icon = "fa-solid fa-user-gear"
        column_list = [UserSpeakerPreference.id, UserSpeakerPreference.user_id, UserSpeakerPreference.speaker_id, UserSpeakerPreference.created_at]
        column_sortable_list = [UserSpeakerPreference.id, UserSpeakerPreference.created_at]
    
    class OnboardingQuestionAdmin(ModelView, model=OnboardingQuestion):
        icon = "fa-solid fa-clipboard-list"
        column_list = [OnboardingQuestion.id, OnboardingQuestion.created_at, OnboardingQuestion.updated_at]
        column_sortable_list = [OnboardingQuestion.id, OnboardingQuestion.created_at]
    
    class SermonAdmin(ModelView, model=Sermon):
        icon = "fa-solid fa-video"
        column_list = [Sermon.id, Sermon.title, Sermon.speaker_id, Sermon.is_clip, Sermon.created_at]
        column_searchable_list = [Sermon.title, Sermon.description]
        column_sortable_list = [Sermon.id, Sermon.title, Sermon.created_at]
        column_details_list = [Sermon.id, Sermon.title, Sermon.description, Sermon.gcs_url, Sermon.is_clip, Sermon.speaker_id, Sermon.created_at, Sermon.updated_at]
    
    class UserSermonPreferenceAdmin(ModelView, model=UserSermonPreference):
        icon = "fa-solid fa-thumbs-up"
        column_list = [UserSermonPreference.id, UserSermonPreference.user_id, UserSermonPreference.sermon_id, UserSermonPreference.preference, UserSermonPreference.created_at]
        column_searchable_list = [UserSermonPreference.preference]
        column_sortable_list = [UserSermonPreference.id, UserSermonPreference.created_at]
    
    class FeaturedSermonAdmin(ModelView, model=FeaturedSermon):
        icon = "fa-solid fa-star"
        column_list = [FeaturedSermon.id, FeaturedSermon.church_id, FeaturedSermon.sermon_id, FeaturedSermon.sort_order, FeaturedSermon.is_active, FeaturedSermon.created_at]
        column_searchable_list = [FeaturedSermon.church_id, FeaturedSermon.sermon_id]
        column_sortable_list = [FeaturedSermon.id, FeaturedSermon.sort_order, FeaturedSermon.created_at]
    
    # Register admin views
    admin.add_view(ChurchAdmin)
    admin.add_view(SpeakerAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(UserSpeakerPreferenceAdmin)
    admin.add_view(OnboardingQuestionAdmin)
    admin.add_view(SermonAdmin)
    admin.add_view(UserSermonPreferenceAdmin)
    admin.add_view(FeaturedSermonAdmin)
    
    return admin_app

# Create the admin app instance
admin_app = create_admin_app()
