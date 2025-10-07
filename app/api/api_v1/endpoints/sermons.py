from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import Sermon, SermonCreate, SermonUpdate, SermonWithSpeaker

router = APIRouter()

@router.get("/", response_model=List[SermonWithSpeaker])
def get_sermons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    speaker_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all sermons with optional filtering"""
    query = db.query(models.Sermon)
    
    if speaker_id:
        query = query.filter(models.Sermon.speaker_id == speaker_id)
    
    sermons = query.offset(skip).limit(limit).all()
    return sermons

@router.get("/{sermon_id}", response_model=SermonWithSpeaker)
def get_sermon(sermon_id: int, db: Session = Depends(get_db)):
    """Get a specific sermon by ID with speaker information"""
    sermon = db.query(models.Sermon).filter(models.Sermon.id == sermon_id).first()
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    return sermon

@router.post("/", response_model=Sermon)
def create_sermon(sermon: SermonCreate, db: Session = Depends(get_db)):
    """Create a new sermon"""
    # Verify that the speaker exists
    speaker = db.query(models.Speaker).filter(models.Speaker.id == sermon.speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    db_sermon = models.Sermon(**sermon.dict())
    db.add(db_sermon)
    db.commit()
    db.refresh(db_sermon)
    return db_sermon

@router.put("/{sermon_id}", response_model=Sermon)
def update_sermon(
    sermon_id: int, 
    sermon_update: SermonUpdate, 
    db: Session = Depends(get_db)
):
    """Update a sermon"""
    db_sermon = db.query(models.Sermon).filter(models.Sermon.id == sermon_id).first()
    if not db_sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    
    update_data = sermon_update.dict(exclude_unset=True)
    
    # If speaker_id is being updated, verify the speaker exists
    if "speaker_id" in update_data:
        speaker = db.query(models.Speaker).filter(models.Speaker.id == update_data["speaker_id"]).first()
        if not speaker:
            raise HTTPException(status_code=404, detail="Speaker not found")
    
    for field, value in update_data.items():
        setattr(db_sermon, field, value)
    
    db.commit()
    db.refresh(db_sermon)
    return db_sermon

@router.delete("/{sermon_id}")
def delete_sermon(sermon_id: int, db: Session = Depends(get_db)):
    """Delete a sermon"""
    db_sermon = db.query(models.Sermon).filter(models.Sermon.id == sermon_id).first()
    if not db_sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
    
    db.delete(db_sermon)
    db.commit()
    return {"message": "Sermon deleted successfully"}

@router.get("/speaker/{speaker_id}/sermons", response_model=List[Sermon])
def get_speaker_sermons(speaker_id: int, db: Session = Depends(get_db)):
    """Get all sermons for a specific speaker"""
    # Verify that the speaker exists
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    sermons = db.query(models.Sermon).filter(models.Sermon.speaker_id == speaker_id).all()
    return sermons
