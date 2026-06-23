import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from database.models import UploadedFile
from env import UPLOAD_DIR


class FileUploadService:
    @staticmethod
    async def create_file(file: UploadFile, session_id: uuid.UUID, db: AsyncSession) -> UploadedFile:
        try:
            # Save file to disk
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension != ".xlsx":
                raise HTTPException(status_code=400, detail="Only .xlsx files are allowed.")

            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)

            with open(file_path, "wb") as f:
                f.write(await file.read())

            # Create UploadedFile record in the database
            uploaded_file = UploadedFile(
                id=uuid.uuid4(),
                session_id=session_id,
                filename=unique_filename,
                original_filename=file.filename,
                file_size=os.path.getsize(file_path),
                uploaded_at=datetime.utcnow(),
                processing_status="pending",
            )
            db.add(uploaded_file)
            await db.commit()
            await db.refresh(uploaded_file)

            return uploaded_file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    @staticmethod
    async def get_file_by_id(file_id: uuid.UUID, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="File not found.")
            return file
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def list_all_files(session_id: Optional[uuid.UUID], db: AsyncSession) -> List[UploadedFile]:
        try:
            query = select(UploadedFile)
            if session_id:
                query = query.where(UploadedFile.session_id == session_id)
            result = await db.execute(query)
            files = result.scalars().all()
            return files
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def update_file_status(file_id: uuid.UUID, status: str, db: AsyncSession) -> UploadedFile:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="File not found.")

            file.processing_status = status
            await db.commit()
            await db.refresh(file)
            return file
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def delete_file(file_id: uuid.UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
            file = result.scalar_one_or_none()
            if not file:
                raise HTTPException(status_code=404, detail="File not found.")

            file_path = os.path.join(UPLOAD_DIR, file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)

            await db.delete(file)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")