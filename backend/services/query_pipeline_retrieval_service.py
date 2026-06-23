from uuid import UUID
from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
from database.models import DocumentChunk
from datetime import datetime


class RetrievalService:
    @staticmethod
    async def create_chunk(chunk_data: Dict, db: AsyncSession) -> DocumentChunk:
        try:
            new_chunk = DocumentChunk(**chunk_data)
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating chunk: {str(e)}")

    @staticmethod
    async def get_chunk_by_id(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail=f"Chunk with ID {chunk_id} not found")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving chunk: {str(e)}")

    @staticmethod
    async def list_chunks_by_file(file_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.file_id == file_id))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing chunks: {str(e)}")

    @staticmethod
    async def update_chunk(chunk_id: UUID, chunk_data: Dict, db: AsyncSession) -> DocumentChunk:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail=f"Chunk with ID {chunk_id} not found")
            
            for key, value in chunk_data.items():
                setattr(chunk, key, value)
            chunk.updated_at = datetime.utcnow()
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating chunk: {str(e)}")

    @staticmethod
    async def delete_chunk(chunk_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail=f"Chunk with ID {chunk_id} not found")
            
            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting chunk: {str(e)}")

    @staticmethod
    async def retrieve_top_chunks_by_similarity(query_embedding: List[float], top_k: int, db: AsyncSession) -> List[DocumentChunk]:
        try:
            # Using pgvector for cosine similarity
            sql_query = text("""
                SELECT *, embedding <-> :query_embedding AS similarity
                FROM document_chunks
                ORDER BY similarity ASC
                LIMIT :top_k
            """)
            result = await db.execute(sql_query.bindparams(query_embedding=query_embedding, top_k=top_k))
            chunks = result.fetchall()
            if not chunks:
                raise HTTPException(status_code=404, detail="No chunks found matching the query")
            return [DocumentChunk(**dict(row)) for row in chunks]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving top chunks: {str(e)}")