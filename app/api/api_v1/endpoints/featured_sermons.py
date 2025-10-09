from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.database import get_db
from app.db.models import FeaturedSermon, Church, Sermon, Speaker
from app.models.schemas import (
    FeaturedSermon as FeaturedSermonSchema,
    FeaturedSermonCreate,
    FeaturedSermonUpdate,
    FeaturedSermonWithDetails
)

router = APIRouter()

@router.get("/churches/{church_id}/featured-sermons", response_model=List[FeaturedSermonWithDetails])
def get_church_featured_sermons(
    church_id: int,
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get featured sermons for a specific church."""
    # Verify church exists
    church = db.query(Church).filter(Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Build query
    query = db.query(FeaturedSermon).filter(FeaturedSermon.church_id == church_id)
    
    if is_active is not None:
        query = query.filter(FeaturedSermon.is_active == is_active)
    
    # Only return non-clip sermons for featured sermons
    query = query.join(Sermon).filter(Sermon.is_clip == False)
    
    # Order by sort_order, then by created_at
    featured_sermons = query.order_by(FeaturedSermon.sort_order, FeaturedSermon.created_at).all()
    
    # Eager load relationships
    result = []
    for fs in featured_sermons:
        fs_dict = {
            "id": fs.id,
            "church_id": fs.church_id,
            "sermon_id": fs.sermon_id,
            "sort_order": fs.sort_order,
            "is_active": fs.is_active,
            "created_at": fs.created_at,
            "updated_at": fs.updated_at,
            "church": {
                "id": fs.church.id,
                "name": fs.church.name,
                "denomination": fs.church.denomination,
                "description": fs.church.description,
                "image_url": fs.church.image_url,
                "is_active": fs.church.is_active
            } if fs.church else None,
            "sermon": {
                "id": fs.sermon.id,
                "title": fs.sermon.title,
                "description": fs.sermon.description,
                "gcs_url": fs.sermon.gcs_url,
                "is_clip": fs.sermon.is_clip,
                "speaker_id": fs.sermon.speaker_id,
                "created_at": fs.sermon.created_at,
                "updated_at": fs.sermon.updated_at,
                "speaker": {
                    "id": fs.sermon.speaker.id,
                    "name": fs.sermon.speaker.name,
                    "title": fs.sermon.speaker.title,
                    "bio": fs.sermon.speaker.bio,
                    "profile_picture_url": fs.sermon.speaker.profile_picture_url,
                    "teaching_style": fs.sermon.speaker.teaching_style,
                    "bible_approach": fs.sermon.speaker.bible_approach,
                    "environment_style": fs.sermon.speaker.environment_style,
                    "gender": fs.sermon.speaker.gender,
                    "is_recommended": fs.sermon.speaker.is_recommended
                } if fs.sermon.speaker else None
            } if fs.sermon else None
        }
        result.append(fs_dict)
    
    return result

@router.post("/churches/{church_id}/featured-sermons", response_model=FeaturedSermonSchema)
def create_featured_sermon(
    church_id: int,
    featured_sermon: FeaturedSermonCreate,
    db: Session = Depends(get_db)
):
    """Add a sermon to a church's featured sermons."""
    # Verify church exists
    church = db.query(Church).filter(Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Verify sermon exists and is not a clip
    sermon = db.query(Sermon).filter(Sermon.id == featured_sermon.sermon_id).first()
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    
    if sermon.is_clip:
        raise HTTPException(status_code=400, detail="Cannot feature sermon clips. Only full sermons can be featured.")
    
    # Ensure church_id matches
    if featured_sermon.church_id != church_id:
        raise HTTPException(status_code=400, detail="Church ID mismatch")
    
    # Check if already featured
    existing = db.query(FeaturedSermon).filter(
        and_(
            FeaturedSermon.church_id == church_id,
            FeaturedSermon.sermon_id == featured_sermon.sermon_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Sermon is already featured for this church")
    
    # Create featured sermon
    db_featured_sermon = FeaturedSermon(**featured_sermon.dict())
    db.add(db_featured_sermon)
    db.commit()
    db.refresh(db_featured_sermon)
    
    return db_featured_sermon

@router.put("/featured-sermons/{featured_sermon_id}", response_model=FeaturedSermonSchema)
def update_featured_sermon(
    featured_sermon_id: int,
    featured_sermon_update: FeaturedSermonUpdate,
    db: Session = Depends(get_db)
):
    """Update a featured sermon."""
    db_featured_sermon = db.query(FeaturedSermon).filter(FeaturedSermon.id == featured_sermon_id).first()
    if not db_featured_sermon:
        raise HTTPException(status_code=404, detail="Featured sermon not found")
    
    # Update fields
    update_data = featured_sermon_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_featured_sermon, field, value)
    
    db.commit()
    db.refresh(db_featured_sermon)
    
    return db_featured_sermon

@router.delete("/featured-sermons/{featured_sermon_id}")
def delete_featured_sermon(
    featured_sermon_id: int,
    db: Session = Depends(get_db)
):
    """Remove a sermon from featured sermons."""
    db_featured_sermon = db.query(FeaturedSermon).filter(FeaturedSermon.id == featured_sermon_id).first()
    if not db_featured_sermon:
        raise HTTPException(status_code=404, detail="Featured sermon not found")
    
    db.delete(db_featured_sermon)
    db.commit()
    
    return {"message": "Featured sermon removed successfully"}

@router.get("/featured-sermons", response_model=List[FeaturedSermonWithDetails])
def get_all_featured_sermons(
    church_id: Optional[int] = Query(None, description="Filter by church ID"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get all featured sermons with optional filtering."""
    query = db.query(FeaturedSermon)
    
    if church_id:
        query = query.filter(FeaturedSermon.church_id == church_id)
    
    if is_active is not None:
        query = query.filter(FeaturedSermon.is_active == is_active)
    
    # Only return non-clip sermons
    query = query.join(Sermon).filter(Sermon.is_clip == False)
    
    # Order and paginate
    featured_sermons = query.order_by(
        FeaturedSermon.church_id,
        FeaturedSermon.sort_order,
        FeaturedSermon.created_at
    ).offset(offset).limit(limit).all()
    
    # Eager load relationships (same as above)
    result = []
    for fs in featured_sermons:
        fs_dict = {
            "id": fs.id,
            "church_id": fs.church_id,
            "sermon_id": fs.sermon_id,
            "sort_order": fs.sort_order,
            "is_active": fs.is_active,
            "created_at": fs.created_at,
            "updated_at": fs.updated_at,
            "church": {
                "id": fs.church.id,
                "name": fs.church.name,
                "denomination": fs.church.denomination,
                "description": fs.church.description,
                "image_url": fs.church.image_url,
                "is_active": fs.church.is_active
            } if fs.church else None,
            "sermon": {
                "id": fs.sermon.id,
                "title": fs.sermon.title,
                "description": fs.sermon.description,
                "gcs_url": fs.sermon.gcs_url,
                "is_clip": fs.sermon.is_clip,
                "speaker_id": fs.sermon.speaker_id,
                "created_at": fs.sermon.created_at,
                "updated_at": fs.sermon.updated_at,
                "speaker": {
                    "id": fs.sermon.speaker.id,
                    "name": fs.sermon.speaker.name,
                    "title": fs.sermon.speaker.title,
                    "bio": fs.sermon.speaker.bio,
                    "profile_picture_url": fs.sermon.speaker.profile_picture_url,
                    "teaching_style": fs.sermon.speaker.teaching_style,
                    "bible_approach": fs.sermon.speaker.bible_approach,
                    "environment_style": fs.sermon.speaker.environment_style,
                    "gender": fs.sermon.speaker.gender,
                    "is_recommended": fs.sermon.speaker.is_recommended
                } if fs.sermon.speaker else None
            } if fs.sermon else None
        }
        result.append(fs_dict)
    
    return result
