import logging
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Layout
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class FrontendLayoutService:
    @staticmethod
    async def create_layout(layout_data: dict, db: AsyncSession) -> Layout:
        try:
            new_layout = Layout(**layout_data)
            db.add(new_layout)
            await db.commit()
            await db.refresh(new_layout)
            return new_layout
        except SQLAlchemyError as e:
            logger.error(f"Error creating layout: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating layout"
            )

    @staticmethod
    async def get_layout_by_id(layout_id: UUID, db: AsyncSession) -> Layout:
        try:
            result = await db.execute(
                select(Layout).where(Layout.id == layout_id)
            )
            layout = result.scalar_one_or_none()
            if not layout:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Layout with ID {layout_id} not found"
                )
            return layout
        except SQLAlchemyError as e:
            logger.error(f"Error fetching layout by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching layout"
            )

    @staticmethod
    async def list_all_layouts(db: AsyncSession) -> List[Layout]:
        try:
            result = await db.execute(select(Layout))
            layouts = result.scalars().all()
            return layouts
        except SQLAlchemyError as e:
            logger.error(f"Error listing all layouts: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error listing layouts"
            )

    @staticmethod
    async def update_layout(layout_id: UUID, update_data: dict, db: AsyncSession) -> Layout:
        try:
            result = await db.execute(
                select(Layout).where(Layout.id == layout_id)
            )
            layout = result.scalar_one_or_none()
            if not layout:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Layout with ID {layout_id} not found"
                )
            for key, value in update_data.items():
                setattr(layout, key, value)
            db.add(layout)
            await db.commit()
            await db.refresh(layout)
            return layout
        except SQLAlchemyError as e:
            logger.error(f"Error updating layout: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating layout"
            )

    @staticmethod
    async def delete_layout(layout_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(
                select(Layout).where(Layout.id == layout_id)
            )
            layout = result.scalar_one_or_none()
            if not layout:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Layout with ID {layout_id} not found"
                )
            await db.delete(layout)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting layout: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting layout"
            )