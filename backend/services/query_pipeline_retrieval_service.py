import logging
from typing import List, Dict
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import text

from database.models import DocumentChunk

logger = logging.getLogger(__name__)

class RetrievalService:
    @staticmethod
    async def create_chunk(chunk_data: Dict, db: AsyncSession) -> DocumentChunk:
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
    async def update_chunk(chunk_id: str, chunk_data: Dict, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chunk with ID {chunk_id} not found."
                )
            for key, value in chunk_data.items():
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
    async def retrieve_top_chunks_by_similarity(query_embedding: List[float], db: AsyncSession) -> List[DocumentChunk]:
        try:
            sql = text("""
                SELECT * FROM document_chunks
                ORDER BY embedding <-> :query_embedding
                LIMIT 5
            """)
            result = await db.execute(sql.bindparams(query_embedding=query_embedding))
            chunks = result.fetchall()
            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No chunks found for the given query embedding."
                )
            return [DocumentChunk(**dict(row)) for row in chunks]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving top chunks by similarity: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve top chunks."
            )