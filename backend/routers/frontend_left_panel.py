from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import UploadedFile, Session as DBSession
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/frontend-left-panel", tags=["Frontend - Left Panel"])

# Pydantic Schemas
class UploadedFileBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    processing_status: str

class UploadedFileCreate(UploadedFileBase):
    session_id: UUID

class UploadedFileResponse(UploadedFileBase):
    id: UUID
    uploaded_at: datetime

class SessionBase(BaseModel):
    name: str

class SessionCreate(SessionBase):
    user_id: UUID

class SessionResponse(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# File Upload Endpoints
@router.post("/files/upload", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # Save file metadata to the database
        uploaded_file = UploadedFile(
            session_id=session_id,
            filename=file.filename,
            original_filename=file.filename,
            file_size=len(file.file.read()),
            uploaded_at=datetime.utcnow(),
            processing_status="Pending",
        )
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        return uploaded_file
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/files/{file_id}", response_model=UploadedFileResponse)
async def get_file(file_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file

@router.get("/files", response_model=List[UploadedFileResponse])
async def list_files(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    files = db.query(UploadedFile).all()
    return files

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    db.delete(file)
    db.commit()

# Session Management Endpoints
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        new_session = DBSession(
            user_id=session.user_id,
            name=session.name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sessions = db.query(DBSession).all()
    return sessions

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()