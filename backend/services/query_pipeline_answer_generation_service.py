from uuid import UUID
from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from database.models import Message
from google.generativeai import generate_text  # Assuming gemini-2.0-flash SDK is imported as google.generativeai

class AnswerGenerationService:
    async def create_message(self, session_id: UUID, role: str, content: str, citations: Dict, db: AsyncSession) -> Message:
        try:
            new_message = Message(
                id=UUID(),
                session_id=session_id,
                role=role,
                content=content,
                citations=citations,
                created_at=datetime.utcnow()
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_message_by_id(self, message_id: UUID, db: AsyncSession) -> Message:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            return message
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list_all_messages(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        try:
            result = await db.execute(select(Message).where(Message.session_id == session_id))
            messages = result.scalars().all()
            return messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update_message(self, message_id: UUID, updated_content: str, db: AsyncSession) -> Message:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            
            message.content = updated_content
            message.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete_message(self, message_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            
            await db.delete(message)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def generate_answer(self, query: str, context: List[Dict], db: AsyncSession) -> Dict:
        try:
            # Pass the query and context to the Google Generative AI SDK
            response = generate_text(
                model="gemini-2.0-flash",
                prompt=query,
                context=context
            )
            if not response or "text" not in response:
                raise HTTPException(status_code=500, detail="Failed to generate answer")
            
            return {"answer": response["text"], "citations": response.get("citations", {})}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")