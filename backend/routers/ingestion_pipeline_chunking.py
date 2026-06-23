from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.ingestion_pipeline.chunking_service import ChunkingService

router = APIRouter(
    prefix="/ingestion pipeline - chunking",
    tags=["Ingestion Pipeline - Chunking"]
)

# Pydantic schemas
class DocumentChunkBase(BaseModel):
    file_id: UUID
    content: str
    metadata: Optional[dict] = Field(default_factory=dict)
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: int

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: datetime

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None

# Service instance
chunking_service = ChunkingService()

# Routes
@router.get("/", response_model=List[DocumentChunkResponse])
def list_chunks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    chunks = chunking_service.list_chunks(db)
    return [DocumentChunkResponse(**chunk.__dict__) for chunk in chunks]

@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
def get_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    chunk = chunking_service.get_chunk_by_id(chunk_id, db)
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return DocumentChunkResponse(**chunk.__dict__)

@router.post("/", response_model=DocumentChunkResponse)
def create_chunk(chunk_data: DocumentChunkCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    chunk = chunking_service.create_chunks(chunk_data.dict(), db)
    return DocumentChunkResponse(**chunk.__dict__)

@router.put("/{chunk_id}", response_model=DocumentChunkResponse)
def update_chunk(chunk_id: UUID, chunk_data: DocumentChunkUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    chunk = chunking_service.update_chunk(chunk_id, chunk_data.dict(exclude_unset=True), db)
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return DocumentChunkResponse(**chunk.__dict__)

@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    success = chunking_service.delete_chunk(chunk_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")