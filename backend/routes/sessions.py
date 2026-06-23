from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Session as DBSession, Message
from database.config import get_db
from backend.services.session_service import create_session, list_sessions, get_session_messages

router = APIRouter()

# Pydantic schemas
class SessionBase(BaseModel):
    name: str

class SessionCreate(SessionBase):
    user_id: UUID

class SessionResponse(SessionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: dict
    created_at: datetime

# Routes
@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(session: SessionCreate, db: Session = Depends(get_db)):
    """
    Create a new session.
    """
    try:
        new_session = create_session(session=session, db=db)
        return new_session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/", response_model=List[SessionResponse])
async def list_sessions_endpoint(db: Session = Depends(get_db)):
    """
    List all sessions.
    """
    try:
        sessions = list_sessions(db=db)
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages_endpoint(session_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve all messages for a specific session.
    """
    try:
        messages = get_session_messages(session_id=session_id, db=db)
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session messages: {str(e)}"
        )