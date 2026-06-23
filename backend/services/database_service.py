import logging
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.models import User, Session, UploadedFile, Message

logger = logging.getLogger(__name__)

class DatabaseService:
    async def create_user(self, user_data: User, db: AsyncSession) -> User:
        try:
            db.add(user_data)
            await db.commit()
            await db.refresh(user_data)
            return user_data
        except SQLAlchemyError as e:
            logger.error(f"Error creating user: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating user")

    async def get_user_by_id(self, user_id: UUID, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user by ID: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching user")

    async def list_users(self, db: AsyncSession) -> List[User]:
        try:
            result = await db.execute(select(User))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error listing users: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listing users")

    async def update_user(self, user_id: UUID, user_data: User, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            for key, value in user_data.dict(exclude_unset=True).items():
                setattr(user, key, value)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error updating user: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating user")

    async def delete_user(self, user_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            await db.delete(user)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting user: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting user")

    async def create_session(self, session_data: Session, db: AsyncSession) -> Session:
        try:
            db.add(session_data)
            await db.commit()
            await db.refresh(session_data)
            return session_data
        except SQLAlchemyError as e:
            logger.error(f"Error creating session: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating session")

    async def get_session_by_id(self, session_id: UUID, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id).options(joinedload(Session.user)))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error fetching session by ID: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching session")

    async def list_sessions(self, db: AsyncSession) -> List[Session]:
        try:
            result = await db.execute(select(Session).options(joinedload(Session.user)))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error listing sessions: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listing sessions")

    async def update_session(self, session_id: UUID, session_data: Session, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
            for key, value in session_data.dict(exclude_unset=True).items():
                setattr(session, key, value)
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error updating session: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating session")

    async def delete_session(self, session_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
            await db.delete(session)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting session: {e}")
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting session")