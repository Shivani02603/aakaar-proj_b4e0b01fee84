from uuid import UUID
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from database.models import UploadedFile, Session
from pydantic import BaseModel


class UploadedFileCreate(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    processing_status: str


class UploadedFileUpdate(BaseModel):
    filename: str | None = None
    original_filename: str | None = None
    file_size: int | None = None
    processing_status: str | None = None


class SessionCreate(BaseModel):
    user_id: UUID
    name: str


class FrontendLeftPanelService:
    @staticmethod
    async def create_uploaded_file(file_data: UploadedFileCreate, db: AsyncSession) -> UploadedFile:
        try:
            new_file = UploadedFile(
                id=UUID(),
                session_id=file_data.session_id,
                filename=file_data.filename,
                original_filename=file_data.original_filename,
                file_size=file_data.file_size,
                uploaded_at=datetime.utcnow(),
                processing_status=file_data.processing_status,
            )
            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)
            return new_file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating uploaded file: {str(e)}",
            )

    @staticmethod
    async def get_uploaded_file_by_id(file_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Uploaded file with ID {file_id} not found",
                )
            return file
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving uploaded file: {str(e)}",
            )

    @staticmethod
    async def list_all_uploaded_files(db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile))
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing uploaded files: {str(e)}",
            )

    @staticmethod
    async def update_uploaded_file(file_id: UUID, update_data: UploadedFileUpdate, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Uploaded file with ID {file_id} not found",
                )
            for key, value in update_data.dict(exclude_unset=True).items():
                setattr(file, key, value)
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating uploaded file: {str(e)}",
            )

    @staticmethod
    async def delete_uploaded_file(file_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Uploaded file with ID {file_id} not found",
                )
            await db.delete(file)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting uploaded file: {str(e)}",
            )

    @staticmethod
    async def create_session(session_data: SessionCreate, db: AsyncSession) -> Session:
        try:
            new_session = Session(
                id=UUID(),
                user_id=session_data.user_id,
                name=session_data.name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating session: {str(e)}",
            )

    @staticmethod
    async def get_session_by_id(session_id: UUID, db: AsyncSession) -> Session:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session with ID {session_id} not found",
                )
            return session
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving session: {str(e)}",
            )

    @staticmethod
    async def list_all_sessions(db: AsyncSession) -> List[Session]:
        try:
            result = await db.execute(select(Session))
            sessions = result.scalars().all()
            return sessions
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing sessions: {str(e)}",
            )

    @staticmethod
    async def delete_session(session_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session with ID {session_id} not found",
                )
            await db.delete(session)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting session: {str(e)}",
            )