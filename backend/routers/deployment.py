from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Deployment
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/deployment", tags=["Deployment"])

# Pydantic schemas
class DeploymentBase(BaseModel):
    name: str = Field(..., example="My Deployment")
    description: Optional[str] = Field(None, example="Deployment description")
    created_at: Optional[str] = Field(None, example="2023-01-01T00:00:00Z")
    updated_at: Optional[str] = Field(None, example="2023-01-01T00:00:00Z")

class DeploymentCreate(DeploymentBase):
    pass

class DeploymentUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Deployment Name")
    description: Optional[str] = Field(None, example="Updated description")

class DeploymentResponse(DeploymentBase):
    id: UUID

# CRUD endpoints
@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
def create_deployment(deployment: DeploymentCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_deployment = Deployment(**deployment.dict())
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)
    return new_deployment

@router.get("/", response_model=List[DeploymentResponse], status_code=status.HTTP_200_OK)
def list_deployments(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    deployments = db.query(Deployment).all()
    return deployments

@router.get("/{deployment_id}", response_model=DeploymentResponse, status_code=status.HTTP_200_OK)
def get_deployment(deployment_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment

@router.put("/{deployment_id}", response_model=DeploymentResponse, status_code=status.HTTP_200_OK)
def update_deployment(deployment_id: UUID, deployment_update: DeploymentUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    for key, value in deployment_update.dict(exclude_unset=True).items():
        setattr(deployment, key, value)
    db.commit()
    db.refresh(deployment)
    return deployment

@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deployment(deployment_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    db.delete(deployment)
    db.commit()
    return None

# Docker Compose deployment endpoint
@router.post("/docker-compose", status_code=status.HTTP_200_OK)
def deploy_with_docker_compose(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Simulate Docker Compose deployment logic
    try:
        # Placeholder for actual deployment logic
        return {"message": "Deployment initiated using Docker Compose"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))