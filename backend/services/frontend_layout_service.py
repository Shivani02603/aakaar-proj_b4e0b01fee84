from uuid import UUID
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from database.models import Layout
from pydantic import BaseModel, Field


class LayoutBase(BaseModel):
    name: str
    description: str


class LayoutCreate(LayoutBase):
    pass


class LayoutUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class LayoutResponse(LayoutBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class FrontendLayoutService:
    @staticmethod
    async def create_layout(layout_data: LayoutCreate, db: AsyncSession) -> LayoutResponse:
        try:
            new_layout = Layout(
                name=layout_data.name,
                description=layout_data.description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_layout)
            await db.commit()
            await db.refresh(new_layout)
            return LayoutResponse(
                id=new_layout.id,
                name=new_layout.name,
                description=new_layout.description,
                created_at=new_layout.created_at,
                updated_at=new_layout.updated_at,
            )
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating layout: {str(e)}",
            )

    @staticmethod
    async def get_layout_by_id(layout_id: UUID, db: AsyncSession) -> LayoutResponse:
        try:
            result = await db.execute(select(Layout).where(Layout.id == layout_id))
            layout = result.scalar_one_or_none()
            if not layout:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Layout with ID {layout_id} not found",
                )
            return LayoutResponse(
                id=layout.id,
                name=layout.name,
                description=layout.description,
                created_at=layout.created_at,
                updated_at=layout.updated_at,
            )
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving layout: {str(e)}",
            )

    @staticmethod
    async def list_all_layouts(db: AsyncSession) -> List[LayoutResponse]:
        try:
            result = await db.execute(select(Layout))
            layouts = result.scalars().all()
            return [
                LayoutResponse(
                    id=layout.id,
                    name=layout.name,
                    description=layout.description,
                    created_at=layout.created_at,
                    updated_at=layout.updated_at,
                )
                for layout in layouts
            ]
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing layouts: {str(e)}",
            )

    @staticmethod
    async def update_layout(layout_id: UUID, layout_update: LayoutUpdate, db: AsyncSession) -> LayoutResponse:
        try:
            result = await db.execute(select(Layout).where(Layout.id == layout_id))
            layout = result.scalar_one_or_none()
            if not layout:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Layout with ID {layout_id} not found",
                )
            if layout_update.name is not None:
                layout.name = layout_update.name
            if layout_update.description is not None:
                layout.description = layout_update.description
            layout.updated_at = datetime.utcnow()
            db.add(layout)
            await db.commit()
            await db.refresh(layout)
            return LayoutResponse(
                id=layout.id,
                name=layout.name,
                description=layout.description,
                created_at=layout.created_at,
                updated_at=layout.updated_at,
            )
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating layout: {str(e)}",
            )

    @staticmethod
    async def delete_layout(layout_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Layout).where(Layout.id == layout_id))
            layout = result.scalar_one_or_none()
            if not layout:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Layout with ID {layout_id} not found",
                )
            await db.delete(layout)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting layout: {str(e)}",
            )