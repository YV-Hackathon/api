from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.models.schemas import Church, ChurchWithSpeakers

router = APIRouter()

@router.get("/", response_model=List[ChurchWithSpeakers])
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
    """Get a specific church by ID with speakers"""
    church = db.query(models.Church).filter(models.Church.id == church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return church
