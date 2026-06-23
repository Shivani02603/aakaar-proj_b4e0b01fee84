from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Message
from database.config import get_db
from backend.services.auth import get_current_user
from google.generativeai import generate_answer  # Assuming gemini-2.0-flash SDK is imported as google.generativeai

router = APIRouter(
    prefix="/query pipeline - answer generation",
    tags=["Query Pipeline - Answer Generation"]
)

# Pydantic schemas
class AnswerRequest(BaseModel):
    session_id: UUID
    question: str

class AnswerResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: Optional[Dict[str, str]] = None
    created_at: str

class MessageCreate(BaseModel):
    session_id: UUID
    role: str
    content: str
    citations: Optional[Dict[str, str]] = None

class MessageUpdate(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None
    citations: Optional[Dict[str, str]] = None

# Helper function to generate answer using Google Generative AI SDK
async def generate_answer_with_gemini(question: str, context: List[str]) -> Dict:
    try:
        response = generate_answer(question=question, context=context)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

# Endpoint to generate an answer
@router.post("/generate", response_model=AnswerResponse)
async def generate_answer_endpoint(request: AnswerRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        # Retrieve context from the database (mocked for now)
        context = ["Example context 1", "Example context 2"]  # Replace with actual retrieval logic

        # Generate answer using Google Generative AI SDK
        answer_data = await generate_answer_with_gemini(request.question, context)

        # Save the generated answer as a message in the database
        new_message = Message(
            id=UUID(answer_data.get("id")),
            session_id=request.session_id,
            role="assistant",
            content=answer_data.get("content"),
            citations=answer_data.get("citations"),
            created_at=answer_data.get("created_at")
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)

        return AnswerResponse(
            id=new_message.id,
            session_id=new_message.session_id,
            role=new_message.role,
            content=new_message.content,
            citations=new_message.citations,
            created_at=new_message.created_at.isoformat()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# CRUD endpoints for messages
@router.get("/", response_model=List[AnswerResponse])
async def list_messages(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        messages = db.query(Message).all()
        return [
            AnswerResponse(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                citations=message.citations,
                created_at=message.created_at.isoformat()
            )
            for message in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@router.get("/{message_id}", response_model=AnswerResponse)
async def get_message(message_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return AnswerResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            created_at=message.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving message: {str(e)}")

@router.post("/", response_model=AnswerResponse)
async def create_message(request: MessageCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        new_message = Message(
            id=UUID(),
            session_id=request.session_id,
            role=request.role,
            content=request.content,
            citations=request.citations,
            created_at=datetime.utcnow()
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return AnswerResponse(
            id=new_message.id,
            session_id=new_message.session_id,
            role=new_message.role,
            content=new_message.content,
            citations=new_message.citations,
            created_at=new_message.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating message: {str(e)}")

@router.put("/{message_id}", response_model=AnswerResponse)
async def update_message(message_id: UUID, request: MessageUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        if request.role:
            message.role = request.role
        if request.content:
            message.content = request.content
        if request.citations:
            message.citations = request.citations
        db.commit()
        db.refresh(message)
        return AnswerResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            created_at=message.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating message: {str(e)}")

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        db.delete(message)
        db.commit()
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")