from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Layout
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/frontend-layout", tags=["Frontend - Layout"])

# Pydantic schemas
class LayoutBase(BaseModel):
    name: str = Field(..., example="Two-Panel Layout")
    description: Optional[str] = Field(None, example="A layout with two panels for better organization.")

class LayoutCreate(LayoutBase):
    pass

class LayoutUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Layout Name")
    description: Optional[str] = Field(None, example="Updated description for the layout.")

class LayoutResponse(LayoutBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.get("/", response_model=List[LayoutResponse])
def list_layouts(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    layouts = db.query(Layout).all()
    return layouts

@router.get("/{layout_id}", response_model=LayoutResponse)
def get_layout(layout_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layout not found")
    return layout

@router.post("/", response_model=LayoutResponse, status_code=status.HTTP_201_CREATED)
def create_layout(layout: LayoutCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_layout = Layout(**layout.dict())
    db.add(new_layout)
    db.commit()
    db.refresh(new_layout)
    return new_layout

@router.put("/{layout_id}", response_model=LayoutResponse)
def update_layout(layout_id: UUID, layout_update: LayoutUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layout not found")
    
    for key, value in layout_update.dict(exclude_unset=True).items():
        setattr(layout, key, value)
    
    layout.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(layout)
    return layout

@router.delete("/{layout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_layout(layout_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    layout = db.query(Layout).filter(Layout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layout not found")
    
    db.delete(layout)
    db.commit()
    return None