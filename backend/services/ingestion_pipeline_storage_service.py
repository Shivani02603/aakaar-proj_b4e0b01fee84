from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk
from datetime import datetime


class StorageService:
    @staticmethod
    async def create_chunk(chunk_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Create a new document chunk and store it in the database.
        """
        try:
            new_chunk = DocumentChunk(**chunk_data)
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create chunk: {str(e)}")

    @staticmethod
    async def get_chunk_by_id(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        """
        Retrieve a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail=f"Chunk with ID {chunk_id} not found")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve chunk: {str(e)}")

    @staticmethod
    async def list_chunks_by_file(file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        """
        List all chunks associated with a specific file ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list chunks: {str(e)}")

    @staticmethod
    async def update_chunk(chunk_id: UUID, update_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Update a document chunk with new data.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail=f"Chunk with ID {chunk_id} not found")

            for key, value in update_data.items():
                setattr(chunk, key, value)

            chunk.updated_at = datetime.utcnow()
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update chunk: {str(e)}")

    @staticmethod
    async def delete_chunk(chunk_id: UUID, db: AsyncSession) -> None:
        """
        Delete a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail=f"Chunk with ID {chunk_id} not found")

            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete chunk: {str(e)}")

    @staticmethod
    async def store_vectors(vectors: List[dict], db: AsyncSession) -> None:
        """
        Store generated vectors in the database.
        """
        try:
            for vector_data in vectors:
                new_chunk = DocumentChunk(**vector_data)
                db.add(new_chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to store vectors: {str(e)}")