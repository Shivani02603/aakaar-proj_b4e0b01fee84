import logging
from typing import List, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.models import DocumentChunk, UploadedFile

logger = logging.getLogger(__name__)

class SourceCitationService:
    @staticmethod
    async def create_citation(chunk_data: Dict, db: AsyncSession) -> DocumentChunk:
        try:
            new_chunk = DocumentChunk(**chunk_data)
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except SQLAlchemyError as e:
            logger.error(f"Error creating citation: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create citation."
            )

    @staticmethod
    async def get_citation_by_id(chunk_id: str, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(
                select(DocumentChunk).where(DocumentChunk.id == chunk_id)
            )
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {chunk_id} not found."
                )
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving citation by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve citation."
            )

    @staticmethod
    async def list_all_citations(db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            logger.error(f"Error listing all citations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list citations."
            )

    @staticmethod
    async def update_citation(chunk_id: str, update_data: Dict, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(
                select(DocumentChunk).where(DocumentChunk.id == chunk_id)
            )
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {chunk_id} not found."
                )
            for key, value in update_data.items():
                setattr(chunk, key, value)
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error updating citation: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update citation."
            )

    @staticmethod
    async def delete_citation(chunk_id: str, db: AsyncSession) -> None:
        try:
            result = await db.execute(
                select(DocumentChunk).where(DocumentChunk.id == chunk_id)
            )
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {chunk_id} not found."
                )
            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting citation: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete citation."
            )

    @staticmethod
    async def generate_answer_with_citations(query: str, session_id: str, db: AsyncSession) -> Dict:
        try:
            # Example logic for generating an answer with citations
            # This assumes some external logic for querying embeddings and retrieving context
            result = await db.execute(
                select(DocumentChunk, UploadedFile)
                .join(UploadedFile, DocumentChunk.file_id == UploadedFile.id)
                .where(DocumentChunk.session_id == session_id)
            )
            chunks = result.all()
            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No citations found for the given session."
                )
            
            citations = [
                {
                    "filename": chunk.UploadedFile.filename,
                    "row_range": f"{chunk.DocumentChunk.row_start}-{chunk.DocumentChunk.row_end}",
                }
                for chunk in chunks
            ]
            answer = {
                "query": query,
                "citations": citations,
            }
            return answer
        except SQLAlchemyError as e:
            logger.error(f"Error generating answer with citations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate answer with citations."
            )