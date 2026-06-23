from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import UploadedFile, Session as DBSession
from database.config import get_db
from backend.services.file_service import create_uploaded_file, list_uploaded_files, get_uploaded_file_by_id, update_uploaded_file, delete_uploaded_file
from backend.services.session_service import create_session, list_sessions, get_session_by_id, delete_session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/frontend-left-panel", tags=["Frontend - Left Panel"])

# Pydantic Schemas
class UploadedFileBase(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: datetime
    processing_status: str

class UploadedFileCreate(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int

class UploadedFileResponse(UploadedFileBase):
    id: UUID

class UploadedFileUpdate(BaseModel):
    processing_status: Optional[str]

class SessionBase(BaseModel):
    name: str

class SessionCreate(BaseModel):
    name: str

class SessionResponse(SessionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

# Dependency for JWT authentication
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()), db: Session = Depends(get_db)):
    # Placeholder for actual user authentication logic
    # Replace with proper JWT decoding and user fetching
    user = {"id": UUID("12345678-1234-5678-1234-567812345678")}  # Mock user
    return user

# File Upload Endpoints
@router.post("/files", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        file_data = {
            "session_id": session_id,
            "filename": file.filename,
            "original_filename": file.filename,
            "file_size": len(file.file.read()),
        }
        uploaded_file = create_uploaded_file(file_data, db)
        return uploaded_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files", response_model=List[UploadedFileResponse])
async def list_files(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        files = list_uploaded_files(db)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}", response_model=UploadedFileResponse)
async def get_file(file_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        file = get_uploaded_file_by_id(file_id, db)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return file
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/files/{file_id}", response_model=UploadedFileResponse)
async def update_file(
    file_id: UUID,
    update_data: UploadedFileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        updated_file = update_uploaded_file(file_id, update_data.dict(exclude_unset=True), db)
        if not updated_file:
            raise HTTPException(status_code=404, detail="File not found")
        return updated_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        delete_uploaded_file(file_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(session: SessionCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        session_data = {
            "name": session.name,
            "user_id": current_user["id"],
        }
        new_session = create_session(session_data, db)
        return new_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions_endpoint(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        sessions = list_sessions(db)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        session = get_session_by_id(session_id, db)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_endpoint(session_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        delete_session(session_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))