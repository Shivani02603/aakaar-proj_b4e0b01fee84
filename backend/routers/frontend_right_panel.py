from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(
    prefix="/frontend-right-panel",
    tags=["Frontend - Right Panel"]
)

# Pydantic schemas
class MessageBase(BaseModel):
    session_id: UUID
    role: str
    content: str
    citations: Optional[dict] = None

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None
    citations: Optional[dict] = None

class MessageResponse(MessageBase):
    id: UUID
    created_at: datetime

# CRUD endpoints for messages

@router.get("/messages", response_model=List[MessageResponse])
def list_messages(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    messages = db.query(Message).all()
    return [
        MessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            created_at=message.created_at
        )
        for message in messages
    ]

@router.get("/messages/{message_id}", response_model=MessageResponse)
def get_message(message_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        citations=message.citations,
        created_at=message.created_at
    )

@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message: MessageCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_message = Message(
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        citations=message.citations,
        created_at=datetime.utcnow()
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return MessageResponse(
        id=new_message.id,
        session_id=new_message.session_id,
        role=new_message.role,
        content=new_message.content,
        citations=new_message.citations,
        created_at=new_message.created_at
    )

@router.put("/messages/{message_id}", response_model=MessageResponse)
def update_message(message_id: UUID, message_update: MessageUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    
    if message_update.role is not None:
        message.role = message_update.role
    if message_update.content is not None:
        message.content = message_update.content
    if message_update.citations is not None:
        message.citations = message_update.citations
    
    db.commit()
    db.refresh(message)
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        citations=message.citations,
        created_at=message.created_at
    )

@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    db.delete(message)
    db.commit()
    return None