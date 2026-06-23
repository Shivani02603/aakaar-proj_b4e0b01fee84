from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import User, Session
from database.config import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/frontend", tags=["Frontend"])

# Dependency for JWT authentication
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()), db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    user = decode_access_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    db_user = db.query(User).filter(User.id == user["id"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

# Pydantic schemas
class UserBase(BaseModel):
    email: str = Field(..., example="user@example.com")

class UserCreate(UserBase):
    password: str = Field(..., example="securepassword")

class UserResponse(UserBase):
    id: UUID
    created_at: datetime

class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, example="newemail@example.com")
    password: Optional[str] = Field(None, example="newsecurepassword")

class SessionBase(BaseModel):
    name: str = Field(..., example="My Session")

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

class SessionUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Session Name")

# Endpoints
@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, password=hashed_password, created_at=datetime.utcnow())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_update.email:
        user.email = user_update.email
    if user_update.password:
        user.password = hash_password(user_update.password)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(Session).filter(Session.user_id == current_user.id).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_session = Session(name=session.name, user_id=current_user.id, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: UUID, session_update: SessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_update.name:
        session.name = session_update.name
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(Session).filter(Session.id == session_id, Session.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
    return