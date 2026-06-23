import logging
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk
from ai.embeddings import get_embedding

logger = logging.getLogger(__name__)

class EmbeddingService:
    @staticmethod
    async def create_embedding(chunk_id: str, db: AsyncSession) -> DocumentChunk:
        try:
            # Fetch the chunk by ID
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"DocumentChunk with id {chunk_id} not found."
                )

            # Generate embedding for the chunk content
            embedding = get_embedding([chunk.content])
            if not embedding or len(embedding) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate embedding for the chunk content."
                )

            # Update the chunk with the generated embedding
            chunk.embedding = embedding[0]
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)

            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating embedding: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating the embedding."
            )

    @staticmethod
    async def get_embedding_by_id(chunk_id: str, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"DocumentChunk with id {chunk_id} not found."
                )

            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching embedding by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while fetching the embedding."
            )

    @staticmethod
    async def list_all_embeddings(db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing all embeddings: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while listing all embeddings."
            )

    @staticmethod
    async def update_embedding(chunk_id: str, new_content: str, db: AsyncSession) -> DocumentChunk:
        try:
            # Fetch the chunk by ID
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"DocumentChunk with id {chunk_id} not found."
                )

            # Update the chunk content and regenerate embedding
            chunk.content = new_content
            embedding = get_embedding([new_content])
            if not embedding or len(embedding) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate embedding for the updated content."
                )

            chunk.embedding = embedding[0]
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)

            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating embedding: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the embedding."
            )

    @staticmethod
    async def delete_embedding(chunk_id: str, db: AsyncSession) -> None:
        try:
            # Fetch the chunk by ID
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"DocumentChunk with id {chunk_id} not found."
                )

            # Delete the chunk
            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting embedding: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the embedding."
            )