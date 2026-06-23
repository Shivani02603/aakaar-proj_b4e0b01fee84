import logging
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import User, Session

logger = logging.getLogger(__name__)

class FrontendService:
    async def create_user(self, user_data: dict, db: AsyncSession) -> User:
        try:
            new_user = User(**user_data)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except SQLAlchemyError as e:
            logger.error(f"Error creating user: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user."
            )

    async def get_user_by_id(self, user_id: UUID, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user."
            )

    async def list_all_users(self, db: AsyncSession) -> List[User]:
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            return users
        except SQLAlchemyError as e:
            logger.error(f"Error listing all users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list users."
            )

    async def update_user_email(self, user_id: UUID, new_email: str, db: AsyncSession) -> User:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )
            user.email = new_email
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error updating user email: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user email."
            )

    async def delete_user(self, user_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )
            await db.delete(user)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting user: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user."
            )

    async def create_session(self, session_data: dict, db: AsyncSession) -> Session:
        try:
            new_session = Session(**session_data)
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        except SQLAlchemyError as e:
            logger.error(f"Error creating session: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session."
            )

    async def get_session_by_id(self, session_id: UUID, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found."
                )
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error fetching session by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch session."
            )

    async def list_all_sessions(self, db: AsyncSession) -> List[Session]:
        try:
            result = await db.execute(select(Session))
            sessions = result.scalars().all()
            return sessions
        except SQLAlchemyError as e:
            logger.error(f"Error listing all sessions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list sessions."
            )

    async def update_session_name(self, session_id: UUID, new_name: str, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found."
                )
            session.name = new_name
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error updating session name: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update session name."
            )

    async def delete_session(self, session_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found."
                )
            await db.delete(session)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting session: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete session."
            )