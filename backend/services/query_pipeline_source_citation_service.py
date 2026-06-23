from uuid import UUID
from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from database.models import DocumentChunk
from database.models import SourceCitation
from sqlalchemy.orm import joinedload


class SourceCitationService:
    async def create_citation(self, citation_data: Dict, db: AsyncSession) -> SourceCitation:
        try:
            new_citation = SourceCitation(**citation_data)
            db.add(new_citation)
            await db.commit()
            await db.refresh(new_citation)
            return new_citation
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating citation: {str(e)}")

    async def get_citation_by_id(self, citation_id: UUID, db: AsyncSession) -> SourceCitation:
        try:
            result = await db.execute(
                select(SourceCitation).where(SourceCitation.id == citation_id)
            )
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(status_code=404, detail="Citation not found")
            return citation
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving citation: {str(e)}")

    async def list_all_citations(self, db: AsyncSession) -> List[SourceCitation]:
        try:
            result = await db.execute(select(SourceCitation))
            citations = result.scalars().all()
            return citations
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing citations: {str(e)}")

    async def update_citation(self, citation_id: UUID, citation_update: Dict, db: AsyncSession) -> SourceCitation:
        try:
            result = await db.execute(
                select(SourceCitation).where(SourceCitation.id == citation_id)
            )
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(status_code=404, detail="Citation not found")

            for key, value in citation_update.items():
                setattr(citation, key, value)

            db.add(citation)
            await db.commit()
            await db.refresh(citation)
            return citation
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating citation: {str(e)}")

    async def delete_citation(self, citation_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(
                select(SourceCitation).where(SourceCitation.id == citation_id)
            )
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(status_code=404, detail="Citation not found")

            await db.delete(citation)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting citation: {str(e)}")

    async def generate_answer_with_citations(self, query: str, db: AsyncSession) -> Dict:
        try:
            # Example logic for generating an answer with citations
            result = await db.execute(
                select(DocumentChunk).options(joinedload(DocumentChunk.source_citations))
            )
            chunks = result.scalars().all()

            # Simulate answer generation and citation extraction
            answer = f"Generated answer for query: {query}"
            citations = [
                {
                    "filename": chunk.metadata.get("filename"),
                    "row_range": f"{chunk.row_start}-{chunk.row_end}",
                }
                for chunk in chunks
            ]

            return {"answer": answer, "citations": citations}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error generating answer with citations: {str(e)}")