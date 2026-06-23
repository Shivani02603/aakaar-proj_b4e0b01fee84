import logging
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from database.models import DocumentChunk
from ai.embeddings import get_embedding

logger = logging.getLogger(__name__)

class StorageService:
    @staticmethod
    async def create_chunk(chunk_data: dict, db: AsyncSession) -> DocumentChunk:
        try:
            chunk = DocumentChunk(**chunk_data)
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error creating chunk: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chunk."
            )

    @staticmethod
    async def get_chunk_by_id(chunk_id: str, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chunk with ID {chunk_id} not found."
                )
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving chunk by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve chunk."
            )

    @staticmethod
    async def list_chunks_by_file(file_id: str, db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            logger.error(f"Error listing chunks by file ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list chunks."
            )

    @staticmethod
    async def update_chunk(chunk_id: str, update_data: dict, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chunk with ID {chunk_id} not found."
                )
            for key, value in update_data.items():
                setattr(chunk, key, value)
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error updating chunk: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update chunk."
            )

    @staticmethod
    async def delete_chunk(chunk_id: str, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chunk with ID {chunk_id} not found."
                )
            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting chunk: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete chunk."
            )

    @staticmethod
    async def store_vectors(chunks: List[DocumentChunk], db: AsyncSession) -> None:
        try:
            for chunk in chunks:
                embedding = get_embedding([chunk.content])[0]
                chunk.embedding = embedding
                db.add(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error storing vectors: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store vectors."
            )
        except Exception as e:
            logger.error(f"Unexpected error during vector storage: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store vectors due to an unexpected error."
            )