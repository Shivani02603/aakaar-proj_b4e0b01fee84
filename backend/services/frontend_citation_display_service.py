from uuid import UUID
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from database.models import SourceCitation
from pydantic import BaseModel


class FrontendCitationDisplayService:
    async def create_citation(self, citation_data: dict, db: AsyncSession) -> SourceCitation:
        try:
            new_citation = SourceCitation(**citation_data)
            db.add(new_citation)
            await db.commit()
            await db.refresh(new_citation)
            return new_citation
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating citation: {str(e)}"
            )

    async def get_citation_by_id(self, citation_id: UUID, db: AsyncSession) -> SourceCitation:
        try:
            result = await db.execute(select(SourceCitation).where(SourceCitation.id == citation_id))
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {citation_id} not found"
                )
            return citation
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving citation: {str(e)}"
            )

    async def list_all_citations(self, db: AsyncSession) -> List[SourceCitation]:
        try:
            result = await db.execute(select(SourceCitation))
            citations = result.scalars().all()
            return citations
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing citations: {str(e)}"
            )

    async def update_citation(self, citation_id: UUID, citation_update: dict, db: AsyncSession) -> SourceCitation:
        try:
            result = await db.execute(select(SourceCitation).where(SourceCitation.id == citation_id))
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {citation_id} not found"
                )
            for key, value in citation_update.items():
                setattr(citation, key, value)
            citation.updated_at = datetime.utcnow()
            db.add(citation)
            await db.commit()
            await db.refresh(citation)
            return citation
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating citation: {str(e)}"
            )

    async def delete_citation(self, citation_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(SourceCitation).where(SourceCitation.id == citation_id))
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {citation_id} not found"
                )
            await db.delete(citation)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting citation: {str(e)}"
            )