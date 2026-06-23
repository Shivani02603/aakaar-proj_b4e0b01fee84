import logging
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Deployment
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class DeploymentService:
    @staticmethod
    async def create_deployment(deployment_data: dict, db: AsyncSession) -> Deployment:
        try:
            deployment = Deployment(**deployment_data)
            db.add(deployment)
            await db.commit()
            await db.refresh(deployment)
            return deployment
        except SQLAlchemyError as e:
            logger.error(f"Error creating deployment: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create deployment."
            )

    @staticmethod
    async def get_deployment_by_id(deployment_id: UUID, db: AsyncSession) -> Deployment:
        try:
            result = await db.execute(
                select(Deployment).where(Deployment.id == deployment_id)
            )
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found."
                )
            return deployment
        except SQLAlchemyError as e:
            logger.error(f"Error fetching deployment by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch deployment."
            )

    @staticmethod
    async def list_all_deployments(db: AsyncSession) -> List[Deployment]:
        try:
            result = await db.execute(select(Deployment))
            deployments = result.scalars().all()
            return deployments
        except SQLAlchemyError as e:
            logger.error(f"Error listing deployments: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list deployments."
            )

    @staticmethod
    async def update_deployment(deployment_id: UUID, update_data: dict, db: AsyncSession) -> Deployment:
        try:
            result = await db.execute(
                select(Deployment).where(Deployment.id == deployment_id)
            )
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found."
                )
            for key, value in update_data.items():
                setattr(deployment, key, value)
            db.add(deployment)
            await db.commit()
            await db.refresh(deployment)
            return deployment
        except SQLAlchemyError as e:
            logger.error(f"Error updating deployment: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update deployment."
            )

    @staticmethod
    async def delete_deployment(deployment_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(
                select(Deployment).where(Deployment.id == deployment_id)
            )
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found."
                )
            await db.delete(deployment)
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting deployment: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete deployment."
            )