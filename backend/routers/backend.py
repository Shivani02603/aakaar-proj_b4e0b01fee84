from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import User, Session as DBSession, UploadedFile
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/backend", tags=["Backend"])

# Pydantic Schemas
class UserBase(BaseModel):
    email: str = Field(..., example="user@example.com")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    created_at: datetime

class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, example="new_email@example.com")

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

class UploadedFileBase(BaseModel):
    filename: str = Field(..., example="file.txt")
    original_filename: str = Field(..., example="original_file.txt")
    file_size: int = Field(..., example=1024)
    processing_status: str = Field(..., example="pending")

class UploadedFileCreate(UploadedFileBase):
    session_id: UUID

class UploadedFileResponse(UploadedFileBase):
    id: UUID
    session_id: UUID
    uploaded_at: datetime

class UploadedFileUpdate(BaseModel):
    processing_status: Optional[str] = Field(None, example="completed")

# User Endpoints
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, created_at=datetime.utcnow())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_update.email:
        user.email = user_update.email
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
    return None

# Session Endpoints
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_session = DBSession(name=session.name, user_id=current_user.id, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(DBSession).filter(DBSession.user_id == current_user.id).all()

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: UUID, session_update: SessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
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
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
    return None

# UploadedFile Endpoints
@router.post("/files", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
def create_uploaded_file(file: UploadedFileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_file = UploadedFile(
        filename=file.filename,
        original_filename=file.original_filename,
        file_size=file.file_size,
        processing_status=file.processing_status,
        session_id=file.session_id,
        uploaded_at=datetime.utcnow()
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("/files", response_model=List[UploadedFileResponse])
def list_uploaded_files(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(UploadedFile).join(DBSession).filter(DBSession.user_id == current_user.id).all()

@router.get("/files/{file_id}", response_model=UploadedFileResponse)
def get_uploaded_file(file_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).join(DBSession).filter(UploadedFile.id == file_id, DBSession.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file

@router.put("/files/{file_id}", response_model=UploadedFileResponse)
def update_uploaded_file(file_id: UUID, file_update: UploadedFileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).join(DBSession).filter(UploadedFile.id == file_id, DBSession.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if file_update.processing_status:
        file.processing_status = file_update.processing_status
    db.commit()
    db.refresh(file)
    return file

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uploaded_file(file_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).join(DBSession).filter(UploadedFile.id == file_id, DBSession.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    db.delete(file)
    db.commit()
    return None