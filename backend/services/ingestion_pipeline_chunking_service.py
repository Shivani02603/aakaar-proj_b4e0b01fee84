import re
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk
from datetime import datetime


class ChunkingService:
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    @staticmethod
    async def create_chunks(content: str, file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        """
        Split the content into overlapping chunks and store them in the database.
        """
        try:
            tokens = re.findall(r'\S+', content)
            chunks = []
            start = 0

            while start < len(tokens):
                end = min(start + ChunkingService.CHUNK_SIZE, len(tokens))
                chunk_content = ' '.join(tokens[start:end])
                chunk = DocumentChunk(
                    file_id=file_id,
                    content=chunk_content,
                    chunk_index=len(chunks),
                    row_start=start,
                    row_end=end,
                    created_at=datetime.utcnow()
                )
                db.add(chunk)
                chunks.append(chunk)
                start += ChunkingService.CHUNK_SIZE - ChunkingService.CHUNK_OVERLAP

            await db.commit()
            return chunks
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def get_chunk_by_id(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        """
        Retrieve a chunk by its ID.
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
    async def list_chunks_by_file(file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        """
        List all chunks associated with a specific file.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def update_chunk(chunk_id: UUID, update_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Update a chunk's data.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found")

            for key, value in update_data.items():
                if hasattr(chunk, key):
                    setattr(chunk, key, value)

            chunk.updated_at = datetime.utcnow()
            await db.commit()
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def delete_chunk(chunk_id: UUID, db: AsyncSession) -> None:
        """
        Delete a chunk by its ID.
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