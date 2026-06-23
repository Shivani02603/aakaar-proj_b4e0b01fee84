import logging
from uuid import UUID
from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk
from datetime import datetime
from ai.embeddings import get_embedding

logger = logging.getLogger(__name__)

class EmbeddingService:
    @staticmethod
    async def create_embedding(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        try:
            # Fetch the chunk by ID
            query = select(DocumentChunk).where(DocumentChunk.id == chunk_id)
            result = await db.execute(query)
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise HTTPException(status_code=404, detail=f"DocumentChunk with ID {chunk_id} not found.")

            # Generate embedding for the chunk content
            embedding = get_embedding([chunk.content])[0]

            # Update the chunk with the embedding
            chunk.embedding = embedding
            chunk.updated_at = datetime.utcnow()
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)

            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating embedding for chunk {chunk_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error.")
        except Exception as e:
            logger.error(f"Unexpected error while creating embedding for chunk {chunk_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")

    @staticmethod
    async def get_embedding_by_id(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        try:
            query = select(DocumentChunk).where(DocumentChunk.id == chunk_id)
            result = await db.execute(query)
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise HTTPException(status_code=404, detail=f"DocumentChunk with ID {chunk_id} not found.")

            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching embedding for chunk {chunk_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")
        except Exception as e:
            logger.error(f"Unexpected error while fetching embedding for chunk {chunk_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")

    @staticmethod
    async def list_all_embeddings(db: AsyncSession) -> List[DocumentChunk]:
        try:
            query = select(DocumentChunk)
            result = await db.execute(query)
            chunks = result.scalars().all()

            return chunks
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing all embeddings: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")
        except Exception as e:
            logger.error(f"Unexpected error while listing all embeddings: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")

    @staticmethod
    async def update_embedding(chunk_id: UUID, new_content: str, db: AsyncSession) -> DocumentChunk:
        try:
            query = select(DocumentChunk).where(DocumentChunk.id == chunk_id)
            result = await db.execute(query)
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise HTTPException(status_code=404, detail=f"DocumentChunk with ID {chunk_id} not found.")

            # Generate new embedding for the updated content
            embedding = get_embedding([new_content])[0]

            # Update the chunk with the new content and embedding
            chunk.content = new_content
            chunk.embedding = embedding
            chunk.updated_at = datetime.utcnow()
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)

            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating embedding for chunk {chunk_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error.")
        except Exception as e:
            logger.error(f"Unexpected error while updating embedding for chunk {chunk_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")

    @staticmethod
    async def delete_embedding(chunk_id: UUID, db: AsyncSession) -> None:
        try:
            query = select(DocumentChunk).where(DocumentChunk.id == chunk_id)
            result = await db.execute(query)
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise HTTPException(status_code=404, detail=f"DocumentChunk with ID {chunk_id} not found.")

            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting embedding for chunk {chunk_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error.")
        except Exception as e:
            logger.error(f"Unexpected error while deleting embedding for chunk {chunk_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")