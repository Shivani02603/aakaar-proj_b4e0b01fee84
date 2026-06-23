from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database.models import User
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter()

# Pydantic schemas
class UserBase(BaseModel):
    email: str = Field(..., example="user@example.com")

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: str

class UserUpdate(BaseModel):
    email: str = Field(..., example="new_email@example.com")

# Route handlers
@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).all()
    return [
        {"id": str(user.id), "email": user.email, "created_at": user.created_at.isoformat()}
        for user in users
    ]

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    user.email = user_update.email
    db.commit()
    db.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    db.delete(user)
    db.commit()
    return None