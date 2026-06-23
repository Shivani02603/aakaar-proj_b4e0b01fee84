import logging
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Citation

logger = logging.getLogger(__name__)

class FrontendCitationDisplayService:
    @staticmethod
    async def create_citation(citation_data: dict, db: AsyncSession) -> Citation:
        try:
            citation = Citation(**citation_data)
            db.add(citation)
            await db.commit()
            await db.refresh(citation)
            return citation
        except SQLAlchemyError as e:
            logger.error(f"Error creating citation: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create citation."
            )

    @staticmethod
    async def get_citation_by_id(citation_id: UUID, db: AsyncSession) -> Citation:
        try:
            result = await db.execute(select(Citation).where(Citation.id == citation_id))
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {citation_id} not found."
                )
            return citation
        except SQLAlchemyError as e:
            logger.error(f"Error fetching citation by ID {citation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch citation."
            )

    @staticmethod
    async def list_all_citations(db: AsyncSession) -> List[Citation]:
        try:
            result = await db.execute(select(Citation))
            citations = result.scalars().all()
            return citations
        except SQLAlchemyError as e:
            logger.error(f"Error listing all citations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list citations."
            )

    @staticmethod
    async def update_citation(citation_id: UUID, update_data: dict, db: AsyncSession) -> Citation:
        try:
            result = await db.execute(select(Citation).where(Citation.id == citation_id))
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {citation_id} not found."
                )
            for key, value in update_data.items():
                setattr(citation, key, value)
            db.add(citation)
            await db.commit()
            await db.refresh(citation)
            return citation
        except SQLAlchemyError as e:
            logger.error(f"Error updating citation with ID {citation_id}: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update citation."
            )

    @staticmethod
    async def delete_citation(citation_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Citation).where(Citation.id == citation_id))
            citation = result.scalar_one_or_none()
            if not citation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Citation with ID {citation_id} not found."
                )
            await db.delete(citation)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting citation with ID {citation_id}: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete citation."
            )