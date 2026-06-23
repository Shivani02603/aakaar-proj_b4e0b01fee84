from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from database.models import Deployment
from pydantic import BaseModel


class DeploymentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    created_at: datetime = datetime.utcnow()


class DeploymentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    updated_at: datetime = datetime.utcnow()


class DeploymentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class DeploymentService:
    @staticmethod
    async def create_deployment(deployment_data: DeploymentCreate, db: AsyncSession) -> DeploymentResponse:
        try:
            new_deployment = Deployment(
                name=deployment_data.name,
                description=deployment_data.description,
                created_at=deployment_data.created_at,
            )
            db.add(new_deployment)
            await db.commit()
            await db.refresh(new_deployment)
            return DeploymentResponse(
                id=new_deployment.id,
                name=new_deployment.name,
                description=new_deployment.description,
                created_at=new_deployment.created_at,
                updated_at=new_deployment.updated_at,
            )
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create deployment: {str(e)}",
            )

    @staticmethod
    async def get_deployment_by_id(deployment_id: UUID, db: AsyncSession) -> DeploymentResponse:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found.",
                )
            return DeploymentResponse(
                id=deployment.id,
                name=deployment.name,
                description=deployment.description,
                created_at=deployment.created_at,
                updated_at=deployment.updated_at,
            )
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve deployment: {str(e)}",
            )

    @staticmethod
    async def list_all_deployments(db: AsyncSession) -> List[DeploymentResponse]:
        try:
            result = await db.execute(select(Deployment))
            deployments = result.scalars().all()
            return [
                DeploymentResponse(
                    id=deployment.id,
                    name=deployment.name,
                    description=deployment.description,
                    created_at=deployment.created_at,
                    updated_at=deployment.updated_at,
                )
                for deployment in deployments
            ]
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list deployments: {str(e)}",
            )

    @staticmethod
    async def update_deployment(
        deployment_id: UUID, deployment_update: DeploymentUpdate, db: AsyncSession
    ) -> DeploymentResponse:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found.",
                )
            if deployment_update.name:
                deployment.name = deployment_update.name
            if deployment_update.description:
                deployment.description = deployment_update.description
            deployment.updated_at = deployment_update.updated_at
            db.add(deployment)
            await db.commit()
            await db.refresh(deployment)
            return DeploymentResponse(
                id=deployment.id,
                name=deployment.name,
                description=deployment.description,
                created_at=deployment.created_at,
                updated_at=deployment.updated_at,
            )
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update deployment: {str(e)}",
            )

    @staticmethod
    async def delete_deployment(deployment_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Deployment with ID {deployment_id} not found.",
                )
            await db.delete(deployment)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete deployment: {str(e)}",
            )