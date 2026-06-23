from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Message
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.query_pipeline.answer_generation_service import AnswerGenerationService
from datetime import datetime

router = APIRouter(
    prefix="/query pipeline - answer generation",
    tags=["Query Pipeline - Answer Generation"]
)

# Pydantic Schemas
class MessageBase(BaseModel):
    session_id: UUID
    role: str
    content: str
    citations: Optional[dict] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: UUID
    created_at: datetime

class AnswerRequest(BaseModel):
    question: str
    context: List[dict]

class AnswerResponse(BaseModel):
    answer: str
    citations: Optional[dict] = None

# Dependency Injection
def get_answer_generation_service(db: Session = Depends(get_db)):
    return AnswerGenerationService(db)

# Routes
@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AnswerGenerationService(db)
        created_message = service.create_message(message)
        return created_message
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def list_messages(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AnswerGenerationService(db)
        messages = service.list_all_messages()
        return messages
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def get_message_by_id(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AnswerGenerationService(db)
        message = service.get_message_by_id(message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        return message
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def update_message(
    message_id: UUID,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AnswerGenerationService(db)
        updated_message = service.update_message(message_id, message)
        if not updated_message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        return updated_message
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AnswerGenerationService(db)
        deleted = service.delete_message(message_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/generate-answer", response_model=AnswerResponse, status_code=status.HTTP_200_OK)
async def generate_answer(
    request: AnswerRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AnswerGenerationService(db)
        answer = service.generate_answer(request.question, request.context)
        return answer
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))