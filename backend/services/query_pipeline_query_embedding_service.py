import logging
from typing import List, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk
from ai.embeddings import get_embedding

logger = logging.getLogger(__name__)

class QueryEmbeddingService:
    @staticmethod
    async def embed_query(query: str, session_id: str, db: AsyncSession) -> List[float]:
        """
        Embed a user query into a vector representation.
        """
        try:
            embedding = get_embedding([query])
            if not embedding or len(embedding) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate embedding for the query."
                )
            return embedding[0]
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while embedding the query."
            )

    @staticmethod
    async def create_document_chunk(chunk_data: Dict, db: AsyncSession) -> DocumentChunk:
        """
        Create a new document chunk in the database.
        """
        try:
            new_chunk = DocumentChunk(**chunk_data)
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except SQLAlchemyError as e:
            logger.error(f"Error creating document chunk: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating the document chunk."
            )

    @staticmethod
    async def get_document_chunk_by_id(chunk_id: str, db: AsyncSession) -> DocumentChunk:
        """
        Retrieve a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document chunk with ID {chunk_id} not found."
                )
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving document chunk by ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving the document chunk."
            )

    @staticmethod
    async def list_all_document_chunks(db: AsyncSession) -> List[DocumentChunk]:
        """
        List all document chunks in the database.
        """
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            logger.error(f"Error listing all document chunks: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while listing document chunks."
            )

    @staticmethod
    async def update_document_chunk(chunk_id: str, update_data: Dict, db: AsyncSession) -> DocumentChunk:
        """
        Update an existing document chunk.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document chunk with ID {chunk_id} not found."
                )
            for key, value in update_data.items():
                setattr(chunk, key, value)
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error updating document chunk: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the document chunk."
            )

    @staticmethod
    async def delete_document_chunk(chunk_id: str, db: AsyncSession) -> None:
        """
        Delete a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document chunk with ID {chunk_id} not found."
                )
            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting document chunk: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the document chunk."
            )