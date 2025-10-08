from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import (
    ChurchFollowers, 
    ChurchFollowersCreate, 
    ChurchFollowersWithDetails,
    Church,
    User
)

router = APIRouter()

@router.get("/", response_model=List[ChurchFollowersWithDetails])
def get_church_followers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    church_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all church followers with optional filtering"""
    query = db.query(models.ChurchFollowers)
    
    if church_id is not None:
        query = query.filter(models.ChurchFollowers.church_id == church_id)
    
    if user_id is not None:
        query = query.filter(models.ChurchFollowers.user_id == user_id)
    
    followers = query.offset(skip).limit(limit).all()
    return followers

@router.get("/{follow_id}", response_model=ChurchFollowersWithDetails)
def get_church_follower(follow_id: int, db: Session = Depends(get_db)):
    """Get a specific church follower by ID"""
    follower = db.query(models.ChurchFollowers).filter(models.ChurchFollowers.id == follow_id).first()
    if not follower:
        raise HTTPException(status_code=404, detail="Church follower not found")
    return follower

@router.post("/", response_model=ChurchFollowers)
def create_church_follower(follower: ChurchFollowersCreate, db: Session = Depends(get_db)):
    """Follow a church"""
    # Check if church exists
    church = db.query(models.Church).filter(models.Church.id == follower.church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == follower.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing_follow = db.query(models.ChurchFollowers).filter(
        and_(
            models.ChurchFollowers.church_id == follower.church_id,
            models.ChurchFollowers.user_id == follower.user_id
        )
    ).first()
    
    if existing_follow:
        raise HTTPException(status_code=400, detail="User is already following this church")
    
    db_follower = models.ChurchFollowers(**follower.dict())
    db.add(db_follower)
    db.commit()
    db.refresh(db_follower)
    return db_follower

@router.delete("/{follow_id}")
def unfollow_church(follow_id: int, db: Session = Depends(get_db)):
    """Unfollow a church"""
    follower = db.query(models.ChurchFollowers).filter(models.ChurchFollowers.id == follow_id).first()
    if not follower:
        raise HTTPException(status_code=404, detail="Church follower not found")
    
    db.delete(follower)
    db.commit()
    return {"message": "Successfully unfollowed church"}

@router.delete("/church/{church_id}/user/{user_id}")
def unfollow_church_by_ids(church_id: int, user_id: int, db: Session = Depends(get_db)):
    """Unfollow a church by church_id and user_id"""
    follower = db.query(models.ChurchFollowers).filter(
        and_(
            models.ChurchFollowers.church_id == church_id,
            models.ChurchFollowers.user_id == user_id
        )
    ).first()
    
    if not follower:
        raise HTTPException(status_code=404, detail="Church follower not found")
    
    db.delete(follower)
    db.commit()
    return {"message": "Successfully unfollowed church"}

@router.get("/user/{user_id}/churches", response_model=List[Church])
def get_user_followed_churches(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all churches followed by a specific user"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get churches through the relationship
    followers = db.query(models.ChurchFollowers).filter(
        models.ChurchFollowers.user_id == user_id
    ).offset(skip).limit(limit).all()
    
    churches = [follower.church for follower in followers if follower.church]
    return churches

@router.get("/church/{church_id}/followers", response_model=List[User])
def get_church_followers_list(
    church_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all users following a specific church"""
    # Check if church exists
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Get users through the relationship
    followers = db.query(models.ChurchFollowers).filter(
        models.ChurchFollowers.church_id == church_id
    ).offset(skip).limit(limit).all()
    
    users = [follower.user for follower in followers if follower.user]
    return users

@router.get("/user/{user_id}/church/{church_id}/status")
def check_follow_status(user_id: int, church_id: int, db: Session = Depends(get_db)):
    """Check if a user is following a specific church"""
    follower = db.query(models.ChurchFollowers).filter(
        and_(
            models.ChurchFollowers.church_id == church_id,
            models.ChurchFollowers.user_id == user_id
        )
    ).first()
    
    return {"is_following": follower is not None, "follow_id": follower.id if follower else None}
