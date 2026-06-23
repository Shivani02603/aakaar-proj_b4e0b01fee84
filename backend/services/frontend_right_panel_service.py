from uuid import UUID
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from database.models import Message
from pydantic import BaseModel


class FrontendRightPanelService:
    async def create_message(
        self, session_id: UUID, role: str, content: str, citations: dict, db: AsyncSession
    ) -> Message:
        try:
            new_message = Message(
                session_id=session_id,
                role=role,
                content=content,
                citations=citations,
                created_at=datetime.utcnow(),
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create message: {str(e)}",
            )

    async def get_message_by_id(self, message_id: UUID, db: AsyncSession) -> Message:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message with ID {message_id} not found.",
                )
            return message
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve message: {str(e)}",
            )

    async def list_all_messages(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        try:
            result = await db.execute(select(Message).where(Message.session_id == session_id))
            messages = result.scalars().all()
            return messages
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list messages: {str(e)}",
            )

    async def update_message(
        self, message_id: UUID, role: str, content: str, citations: dict, db: AsyncSession
    ) -> Message:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message with ID {message_id} not found.",
                )
            message.role = role
            message.content = content
            message.citations = citations
            message.created_at = datetime.utcnow()
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update message: {str(e)}",
            )

    async def delete_message(self, message_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message with ID {message_id} not found.",
                )
            await db.delete(message)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete message: {str(e)}",
            )