from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/frontend-right-panel", tags=["Frontend - Right Panel"])

# Pydantic schemas
class MessageBase(BaseModel):
    role: str = Field(..., description="Role of the message sender (e.g., 'user', 'assistant')")
    content: str = Field(..., description="Content of the message")
    citations: Optional[dict] = Field(None, description="Citations related to the message")

class MessageCreate(MessageBase):
    session_id: UUID = Field(..., description="ID of the session the message belongs to")

class MessageUpdate(BaseModel):
    content: Optional[str] = Field(None, description="Updated content of the message")
    citations: Optional[dict] = Field(None, description="Updated citations related to the message")

class MessageResponse(MessageBase):
    id: UUID = Field(..., description="Unique identifier of the message")
    session_id: UUID = Field(..., description="ID of the session the message belongs to")
    created_at: datetime = Field(..., description="Timestamp when the message was created")

# Endpoints
@router.get("/", response_model=List[MessageResponse])
def list_messages(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    List all messages for the current user.
    """
    messages = db.query(Message).filter(Message.session_id.in_(current_user["session_ids"])).all()
    return messages

@router.get("/{message_id}", response_model=MessageResponse)
def get_message(message_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get a specific message by ID.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message.session_id not in current_user["session_ids"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return message

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message: MessageCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Create a new message.
    """
    if message.session_id not in current_user["session_ids"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    new_message = Message(**message.dict(), created_at=datetime.utcnow())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@router.put("/{message_id}", response_model=MessageResponse)
def update_message(message_id: UUID, message_update: MessageUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Update an existing message.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message.session_id not in current_user["session_ids"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for key, value in message_update.dict(exclude_unset=True).items():
        setattr(message, key, value)
    db.commit()
    db.refresh(message)
    return message

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Delete a message by ID.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message.session_id not in current_user["session_ids"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    db.delete(message)
    db.commit()