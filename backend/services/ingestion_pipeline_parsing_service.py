import os
import pandas as pd
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, UploadedFile
from datetime import datetime


class ParsingService:
    async def parse_excel_file(self, file_path: str, session_id: str, db: AsyncSession) -> List[DocumentChunk]:
        """
        Parses an Excel file and creates document chunks for each sheet.
        """
        try:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")

            excel_data = pd.ExcelFile(file_path)
            chunks = []

            for sheet_name in excel_data.sheet_names:
                sheet_data = excel_data.parse(sheet_name)
                row_start = 0
                chunk_index = 0

                for _, row in sheet_data.iterrows():
                    row_end = row_start + 1
                    content = row.to_json()

                    chunk = DocumentChunk(
                        file_id=session_id,
                        content=content,
                        metadata={"sheet_name": sheet_name},
                        sheet_name=sheet_name,
                        row_start=row_start,
                        row_end=row_end,
                        chunk_index=chunk_index,
                        created_at=datetime.utcnow()
                    )
                    db.add(chunk)
                    chunks.append(chunk)

                    row_start += 1
                    chunk_index += 1

            await db.commit()
            return chunks

        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="Excel file is empty or invalid")
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    async def create_chunk(self, chunk: DocumentChunk, db: AsyncSession) -> DocumentChunk:
        """
        Creates a new document chunk in the database.
        """
        try:
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_chunk_by_id(self, chunk_id: str, db: AsyncSession) -> DocumentChunk:
        """
        Retrieves a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list_all_chunks(self, db: AsyncSession) -> List[DocumentChunk]:
        """
        Lists all document chunks in the database.
        """
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update_chunk(self, chunk_id: str, updated_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Updates a document chunk with new data.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")

            for key, value in updated_data.items():
                setattr(chunk, key, value)

            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete_chunk(self, chunk_id: str, db: AsyncSession) -> None:
        """
        Deletes a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")

            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")