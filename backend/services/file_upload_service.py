import os
from uuid import UUID
from typing import List
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import UploadedFile
from datetime import datetime

class FileUploadService:
    @staticmethod
    async def create_file(file: UploadFile, session_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            # Save file metadata to the database
            uploaded_file = UploadedFile(
                id=UUID(os.urandom(16).hex()),
                session_id=session_id,
                filename=file.filename,
                original_filename=file.filename,
                file_size=len(await file.read()),
                uploaded_at=datetime.utcnow(),
                processing_status="Pending"
            )
            db.add(uploaded_file)
            await db.commit()
            await db.refresh(uploaded_file)
            return uploaded_file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def get_file_by_id(file_id: UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            return file
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def list_all_files(db: AsyncSession) -> List[UploadedFile]:
        try:
            result = await db.execute(select(UploadedFile))
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def update_file_status(file_id: UUID, status: str, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            file.processing_status = status
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def delete_file(file_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            await db.delete(file)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")