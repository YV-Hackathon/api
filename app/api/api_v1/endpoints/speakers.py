from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import Speaker, SpeakerCreate, SpeakerUpdate, SpeakerWithChurch, Church, convert_speaker_data

router = APIRouter()

@router.get("/", response_model=List[SpeakerWithChurch])
def get_speakers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    church_id: Optional[int] = None,
    is_recommended: Optional[bool] = None,
    teaching_style: Optional[str] = None,
    bible_approach: Optional[str] = None,
    environment_style: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all speakers with optional filtering"""
    query = db.query(models.Speaker)
    
    if church_id:
        query = query.filter(models.Speaker.church_id == church_id)
    
    if is_recommended is not None:
        query = query.filter(models.Speaker.is_recommended == is_recommended)
    
    if teaching_style:
        query = query.filter(models.Speaker.teaching_style == teaching_style)
    
    if bible_approach:
        query = query.filter(models.Speaker.bible_approach == bible_approach)
    
    if environment_style:
        query = query.filter(models.Speaker.environment_style == environment_style)
    
    speakers = query.options(joinedload(models.Speaker.church)).offset(skip).limit(limit).all()
    # Convert speaker data to handle speaking_topics
    converted_speakers = []
    for speaker in speakers:
        converted_data = convert_speaker_data(speaker)
        converted_speakers.append(SpeakerWithChurch(**converted_data))
    return converted_speakers

@router.get("/{speaker_id}", response_model=SpeakerWithChurch)
def get_speaker(speaker_id: int, db: Session = Depends(get_db)):
    """Get a specific speaker by ID with church information"""
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    return speaker

@router.post("/", response_model=Speaker)
def create_speaker(speaker: SpeakerCreate, db: Session = Depends(get_db)):
    """Create a new speaker"""
    db_speaker = models.Speaker(**speaker.dict())
    db.add(db_speaker)
    db.commit()
    db.refresh(db_speaker)
    return db_speaker

@router.put("/{speaker_id}", response_model=Speaker)
def update_speaker(
    speaker_id: int, 
    speaker_update: SpeakerUpdate, 
    db: Session = Depends(get_db)
):
    """Update a speaker"""
    db_speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not db_speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    update_data = speaker_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_speaker, field, value)
    
    db.commit()
    db.refresh(db_speaker)
    return db_speaker

@router.delete("/{speaker_id}")
def delete_speaker(speaker_id: int, db: Session = Depends(get_db)):
    """Delete a speaker"""
    db_speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not db_speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    db.delete(db_speaker)
    db.commit()
    return {"message": "Speaker deleted successfully"}

@router.get("/church/{church_id}/speakers", response_model=List[Speaker])
def get_church_speakers(church_id: int, db: Session = Depends(get_db)):
    """Get all speakers for a specific church"""
    speakers = db.query(models.Speaker).filter(models.Speaker.church_id == church_id).all()
    return speakers

@router.get("/{speaker_id}/churches", response_model=List[Church])
def get_speaker_churches(speaker_id: int, db: Session = Depends(get_db)):
    """Get all churches where a speaker has spoken"""
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    # Return churches where this speaker has spoken (many-to-many relationship)
    return speaker.speaking_churches

@router.post("/{speaker_id}/churches/{church_id}")
def add_speaker_to_church(speaker_id: int, church_id: int, db: Session = Depends(get_db)):
    """Add a speaker to speak at a church"""
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Check if relationship already exists
    if church in speaker.speaking_churches:
        raise HTTPException(status_code=400, detail="Speaker already speaks at this church")
    
    speaker.speaking_churches.append(church)
    db.commit()
    return {"message": "Speaker added to church successfully"}

@router.delete("/{speaker_id}/churches/{church_id}")
def remove_speaker_from_church(speaker_id: int, church_id: int, db: Session = Depends(get_db)):
    """Remove a speaker from speaking at a church"""
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Check if relationship exists
    if church not in speaker.speaking_churches:
        raise HTTPException(status_code=400, detail="Speaker does not speak at this church")
    
    speaker.speaking_churches.remove(church)
    db.commit()
    return {"message": "Speaker removed from church successfully"}
