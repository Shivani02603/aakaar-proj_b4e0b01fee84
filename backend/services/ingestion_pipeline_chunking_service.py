import math
from typing import List, Dict, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from database.models import DocumentChunk, UploadedFile
from datetime import datetime


class ChunkingService:
    @staticmethod
    async def create_chunks(file_id: str, content: str, db: AsyncSession, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """
        Splits the content into overlapping chunks and stores them in the database.
        """
        try:
            chunks = []
            tokens = content.split()
            total_tokens = len(tokens)
            start = 0

            while start < total_tokens:
                end = min(start + chunk_size, total_tokens)
                chunk_content = " ".join(tokens[start:end])
                chunk_index = math.floor(start / chunk_size)

                chunk = DocumentChunk(
                    file_id=file_id,
                    content=chunk_content,
                    metadata={},
                    sheet_name=None,
                    row_start=None,
                    row_end=None,
                    chunk_index=chunk_index,
                    created_at=datetime.utcnow()
                )
                db.add(chunk)
                chunks.append(chunk)
                start += chunk_size - overlap

            await db.commit()
            return [chunk.to_dict() for chunk in chunks]
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def get_chunk_by_id(chunk_id: str, db: AsyncSession) -> DocumentChunk:
        """
        Retrieves a chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def list_chunks_by_file(file_id: str, db: AsyncSession) -> List[DocumentChunk]:
        """
        Lists all chunks associated with a specific file ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def update_chunk(chunk_id: str, updated_data: Dict, db: AsyncSession) -> DocumentChunk:
        """
        Updates a chunk's data.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")

            for key, value in updated_data.items():
                if hasattr(chunk, key):
                    setattr(chunk, key, value)

            chunk.updated_at = datetime.utcnow()
            await db.commit()
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def delete_chunk(chunk_id: str, db: AsyncSession) -> None:
        """
        Deletes a chunk by its ID.
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