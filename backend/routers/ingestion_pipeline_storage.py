from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.ingestion_pipeline.storage_service import StorageService

router = APIRouter(
    prefix="/ingestion pipeline - storage",
    tags=["Ingestion Pipeline - Storage"]
)

# Pydantic Schemas
class DocumentChunkBase(BaseModel):
    file_id: UUID
    content: str
    embedding: List[float]
    metadata: dict
    sheet_name: Optional[str]
    row_start: Optional[int]
    row_end: Optional[int]
    chunk_index: Optional[int]

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

class DocumentChunkUpdate(BaseModel):
    content: Optional[str]
    embedding: Optional[List[float]]
    metadata: Optional[dict]
    sheet_name: Optional[str]
    row_start: Optional[int]
    row_end: Optional[int]
    chunk_index: Optional[int]

# Endpoints
@router.post("/", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
async def create_document_chunk(
    chunk: DocumentChunkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        storage_service = StorageService(db)
        new_chunk = storage_service.create_chunk(chunk.dict())
        return new_chunk
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=List[DocumentChunkResponse], status_code=status.HTTP_200_OK)
async def list_document_chunks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        storage_service = StorageService(db)
        chunks = storage_service.list_all_chunks()
        return chunks
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{chunk_id}", response_model=DocumentChunkResponse, status_code=status.HTTP_200_OK)
async def get_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        storage_service = StorageService(db)
        chunk = storage_service.get_chunk_by_id(chunk_id)
        if not chunk:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
        return chunk
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{chunk_id}", response_model=DocumentChunkResponse, status_code=status.HTTP_200_OK)
async def update_document_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        storage_service = StorageService(db)
        updated_chunk = storage_service.update_chunk(chunk_id, chunk_update.dict(exclude_unset=True))
        if not updated_chunk:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
        return updated_chunk
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        storage_service = StorageService(db)
        deleted = storage_service.delete_chunk(chunk_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
        return {"detail": "Document chunk deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))