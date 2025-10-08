from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import Church, ChurchCreate, ChurchUpdate, ChurchWithSpeakers, Speaker

router = APIRouter()

@router.get("/", response_model=List[Church])
def get_churches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    denomination: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all churches with optional filtering"""
    query = db.query(models.Church)
    
    if is_active is not None:
        query = query.filter(models.Church.is_active == is_active)
    
    if denomination:
        query = query.filter(models.Church.denomination.ilike(f"%{denomination}%"))
    
    churches = query.offset(skip).limit(limit).all()
    return churches

@router.get("/{church_id}", response_model=ChurchWithSpeakers)
def get_church(church_id: int, db: Session = Depends(get_db)):
    """Get a specific church by ID with its speakers"""
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return church

@router.post("/", response_model=Church)
def create_church(church: ChurchCreate, db: Session = Depends(get_db)):
    """Create a new church"""
    db_church = models.Church(**church.dict())
    db.add(db_church)
    db.commit()
    db.refresh(db_church)
    return db_church

@router.put("/{church_id}", response_model=Church)
def update_church(
    church_id: int, 
    church_update: ChurchUpdate, 
    db: Session = Depends(get_db)
):
    """Update a church"""
    db_church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not db_church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    update_data = church_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_church, field, value)
    
    db.commit()
    db.refresh(db_church)
    return db_church

@router.delete("/{church_id}")
def delete_church(church_id: int, db: Session = Depends(get_db)):
    """Delete a church"""
    db_church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not db_church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    db.delete(db_church)
    db.commit()
    return {"message": "Church deleted successfully"}

@router.get("/{church_id}/pastors", response_model=List[Speaker])
def get_church_pastors(church_id: int, db: Session = Depends(get_db)):
    """Get all pastors that speak at a specific church"""
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Return pastors who speak at this church (many-to-many relationship)
    return church.speaking_pastors

@router.post("/{church_id}/pastors/{pastor_id}")
def add_pastor_to_church(church_id: int, pastor_id: int, db: Session = Depends(get_db)):
    """Add a pastor as someone who speaks at this church"""
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    pastor = db.query(models.Speaker).filter(models.Speaker.id == pastor_id).first()
    if not pastor:
        raise HTTPException(status_code=404, detail="Pastor not found")
    
    # Check if relationship already exists
    if pastor in church.speaking_pastors:
        raise HTTPException(status_code=400, detail="Pastor already speaks at this church")
    
    church.speaking_pastors.append(pastor)
    db.commit()
    return {"message": "Pastor added to church successfully"}

@router.delete("/{church_id}/pastors/{pastor_id}")
def remove_pastor_from_church(church_id: int, pastor_id: int, db: Session = Depends(get_db)):
    """Remove a pastor from speaking at this church"""
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    pastor = db.query(models.Speaker).filter(models.Speaker.id == pastor_id).first()
    if not pastor:
        raise HTTPException(status_code=404, detail="Pastor not found")
    
    # Check if relationship exists
    if pastor not in church.speaking_pastors:
        raise HTTPException(status_code=400, detail="Pastor does not speak at this church")
    
    church.speaking_pastors.remove(pastor)
    db.commit()
    return {"message": "Pastor removed from church successfully"}
