from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import (
    SpeakerFollowers, 
    SpeakerFollowersCreate, 
    SpeakerFollowersWithDetails,
    Speaker,
    User
)

router = APIRouter()

@router.get("/", response_model=List[SpeakerFollowersWithDetails])
def get_speaker_followers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    speaker_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all speaker followers with optional filtering"""
    query = db.query(models.SpeakerFollowers)
    
    if speaker_id is not None:
        query = query.filter(models.SpeakerFollowers.speaker_id == speaker_id)
    
    if user_id is not None:
        query = query.filter(models.SpeakerFollowers.user_id == user_id)
    
    followers = query.offset(skip).limit(limit).all()
    return followers

@router.get("/{follow_id}", response_model=SpeakerFollowersWithDetails)
def get_speaker_follower(follow_id: int, db: Session = Depends(get_db)):
    """Get a specific speaker follower by ID"""
    follower = db.query(models.SpeakerFollowers).filter(models.SpeakerFollowers.id == follow_id).first()
    if not follower:
        raise HTTPException(status_code=404, detail="Speaker follower not found")
    return follower

@router.post("/", response_model=SpeakerFollowers)
def create_speaker_follower(follower: SpeakerFollowersCreate, db: Session = Depends(get_db)):
    """Follow a speaker"""
    # Check if speaker exists
    speaker = db.query(models.Speaker).filter(models.Speaker.id == follower.speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == follower.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing_follow = db.query(models.SpeakerFollowers).filter(
        and_(
            models.SpeakerFollowers.speaker_id == follower.speaker_id,
            models.SpeakerFollowers.user_id == follower.user_id
        )
    ).first()
    
    if existing_follow:
        raise HTTPException(status_code=400, detail="User is already following this speaker")
    
    db_follower = models.SpeakerFollowers(**follower.dict())
    db.add(db_follower)
    db.commit()
    db.refresh(db_follower)
    return db_follower

@router.delete("/{follow_id}")
def unfollow_speaker(follow_id: int, db: Session = Depends(get_db)):
    """Unfollow a speaker by follow ID"""
    follower = db.query(models.SpeakerFollowers).filter(models.SpeakerFollowers.id == follow_id).first()
    if not follower:
        raise HTTPException(status_code=404, detail="Speaker follower not found")
    
    db.delete(follower)
    db.commit()
    return {"message": "Successfully unfollowed speaker"}

@router.delete("/speaker/{speaker_id}/user/{user_id}")
def unfollow_speaker_by_ids(speaker_id: int, user_id: int, db: Session = Depends(get_db)):
    """Unfollow a speaker by speaker and user IDs"""
    follower = db.query(models.SpeakerFollowers).filter(
        and_(
            models.SpeakerFollowers.speaker_id == speaker_id,
            models.SpeakerFollowers.user_id == user_id
        )
    ).first()
    
    if not follower:
        raise HTTPException(status_code=404, detail="Speaker follower not found")
    
    db.delete(follower)
    db.commit()
    return {"message": "Successfully unfollowed speaker"}

@router.get("/user/{user_id}/speakers", response_model=List[Speaker])
def get_user_followed_speakers(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all speakers followed by a user"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get followed speakers
    followed_speakers = db.query(models.Speaker).join(
        models.SpeakerFollowers, 
        models.Speaker.id == models.SpeakerFollowers.speaker_id
    ).filter(
        models.SpeakerFollowers.user_id == user_id
    ).offset(skip).limit(limit).all()
    
    return followed_speakers

@router.get("/speaker/{speaker_id}/followers", response_model=List[User])
def get_speaker_followers(
    speaker_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all users following a speaker"""
    # Check if speaker exists
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    # Get followers
    followers = db.query(models.User).join(
        models.SpeakerFollowers,
        models.User.id == models.SpeakerFollowers.user_id
    ).filter(
        models.SpeakerFollowers.speaker_id == speaker_id
    ).offset(skip).limit(limit).all()
    
    return followers

@router.get("/user/{user_id}/speaker/{speaker_id}/status")
def check_follow_status(user_id: int, speaker_id: int, db: Session = Depends(get_db)):
    """Check if a user is following a specific speaker"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if speaker exists
    speaker = db.query(models.Speaker).filter(models.Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    # Check follow status
    follow = db.query(models.SpeakerFollowers).filter(
        and_(
            models.SpeakerFollowers.user_id == user_id,
            models.SpeakerFollowers.speaker_id == speaker_id
        )
    ).first()
    
    return {
        "is_following": follow is not None,
        "follow_id": follow.id if follow else None
    }
