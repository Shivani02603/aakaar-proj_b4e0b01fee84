import logging
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import UploadedFile, Session

logger = logging.getLogger(__name__)

class FrontendLeftPanelService:
    @staticmethod
    async def create_uploaded_file(
        session_id: UUID,
        filename: str,
        original_filename: str,
        file_size: int,
        processing_status: str,
        db: AsyncSession
    ) -> UploadedFile:
        try:
            new_file = UploadedFile(
                session_id=session_id,
                filename=filename,
                original_filename=original_filename,
                file_size=file_size,
                processing_status=processing_status
            )
            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file
        except SQLAlchemyError as e:
            logger.error(f"Error creating uploaded file: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating uploaded file"
            )

    @staticmethod
    async def get_uploaded_file_by_id(file_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Uploaded file with ID {file_id} not found"
                )
            return file
        except SQLAlchemyError as e:
            logger.error(f"Error fetching uploaded file by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching uploaded file"
            )

    @staticmethod
    async def list_all_uploaded_files(db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile))
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            logger.error(f"Error listing all uploaded files: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error listing uploaded files"
            )

    @staticmethod
    async def update_uploaded_file(
        file_id: UUID,
        filename: Optional[str],
        original_filename: Optional[str],
        file_size: Optional[int],
        processing_status: Optional[str],
        db: AsyncSession
    ) -> UploadedFile:
        try:
            file = await FrontendLeftPanelService.get_uploaded_file_by_id(file_id, db)
            if filename:
                file.filename = filename
            if original_filename:
                file.original_filename = original_filename
            if file_size:
                file.file_size = file_size
            if processing_status:
                file.processing_status = processing_status
            db.add(file)
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            logger.error(f"Error updating uploaded file: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating uploaded file"
            )

    @staticmethod
    async def delete_uploaded_file(file_id: UUID, db: AsyncSession) -> None:
        try:
            file = await FrontendLeftPanelService.get_uploaded_file_by_id(file_id, db)
            await db.delete(file)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting uploaded file: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting uploaded file"
            )

    @staticmethod
    async def create_session(
        user_id: UUID,
        name: str,
        db: AsyncSession
    ) -> Session:
        try:
            new_session = Session(
                user_id=user_id,
                name=name
            )
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        except SQLAlchemyError as e:
            logger.error(f"Error creating session: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating session"
            )

    @staticmethod
    async def get_session_by_id(session_id: UUID, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session with ID {session_id} not found"
                )
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error fetching session by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching session"
            )

    @staticmethod
    async def list_all_sessions(db: AsyncSession) -> List[Session]:
        try:
            result = await db.execute(select(Session))
            sessions = result.scalars().all()
            return sessions
        except SQLAlchemyError as e:
            logger.error(f"Error listing all sessions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error listing sessions"
            )

    @staticmethod
    async def update_session(
        session_id: UUID,
        name: Optional[str],
        db: AsyncSession
    ) -> Session:
        try:
            session = await FrontendLeftPanelService.get_session_by_id(session_id, db)
            if name:
                session.name = name
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error updating session: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating session"
            )

    @staticmethod
    async def delete_session(session_id: UUID, db: AsyncSession) -> None:
        try:
            session = await FrontendLeftPanelService.get_session_by_id(session_id, db)
            await db.delete(session)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting session: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting session"
            )