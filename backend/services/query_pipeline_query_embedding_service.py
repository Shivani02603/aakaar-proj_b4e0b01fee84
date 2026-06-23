from uuid import UUID
from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk
from datetime import datetime
from ai.embeddings import get_embedding


class QueryEmbeddingService:
    async def embed_query(self, query: str, session_id: UUID, db: AsyncSession) -> Dict:
        """
        Embed a user query and return the embedding vector.
        """
        try:
            embedding = get_embedding([query])[0]  # Assuming get_embedding returns a list of embeddings
            return {"query": query, "embedding": embedding}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to embed query: {str(e)}")

    async def create_document_chunk(self, chunk_data: Dict, db: AsyncSession) -> DocumentChunk:
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
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create document chunk: {str(e)}")

    async def get_document_chunk_by_id(self, chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        """
        Retrieve a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve document chunk: {str(e)}")

    async def list_all_document_chunks(self, db: AsyncSession) -> List[DocumentChunk]:
        """
        List all document chunks in the database.
        """
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list document chunks: {str(e)}")

    async def update_document_chunk(self, chunk_id: UUID, update_data: Dict, db: AsyncSession) -> DocumentChunk:
        """
        Update a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")

            for key, value in update_data.items():
                setattr(chunk, key, value)

            chunk.updated_at = datetime.utcnow()
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update document chunk: {str(e)}")

    async def delete_document_chunk(self, chunk_id: UUID, db: AsyncSession) -> None:
        """
        Delete a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found")

            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete document chunk: {str(e)}")