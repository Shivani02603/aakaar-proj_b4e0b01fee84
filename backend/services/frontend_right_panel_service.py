import logging
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Message

logger = logging.getLogger(__name__)

class FrontendRightPanelService:
    async def create_message(self, session_id: UUID, role: str, content: str, citations: Optional[dict], db: AsyncSession) -> Message:
        try:
            new_message = Message(
                session_id=session_id,
                role=role,
                content=content,
                citations=citations,
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            logger.error(f"Error creating message: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create message.")

    async def get_message_by_id(self, message_id: UUID, db: AsyncSession) -> Message:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
            return message
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving message by ID: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve message.")

    async def list_all_messages(self, session_id: UUID, db: AsyncSession) -> List[Message]:
        try:
            result = await db.execute(select(Message).where(Message.session_id == session_id))
            messages = result.scalars().all()
            return messages
        except SQLAlchemyError as e:
            logger.error(f"Error listing all messages: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list messages.")

    async def update_message(self, message_id: UUID, role: Optional[str], content: Optional[str], citations: Optional[dict], db: AsyncSession) -> Message:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

            if role is not None:
                message.role = role
            if content is not None:
                message.content = content
            if citations is not None:
                message.citations = citations

            db.add(message)
            await db.commit()
            await db.refresh(message)
            return message
        except SQLAlchemyError as e:
            logger.error(f"Error updating message: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update message.")

    async def delete_message(self, message_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            if not message:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

            await db.delete(message)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting message: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete message.")