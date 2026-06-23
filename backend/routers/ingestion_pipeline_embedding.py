from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from ai.embeddings import get_embedding

router = APIRouter(
    prefix="/ingestion pipeline - embedding",
    tags=["Ingestion Pipeline - Embedding"]
)

# Pydantic Schemas
class DocumentChunkBase(BaseModel):
    file_id: UUID
    content: str
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: int

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    embedding: List[float]
    created_at: datetime

    class Config:
        orm_mode = True

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: Optional[int] = None

# CRUD Endpoints
@router.post("/", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
async def create_document_chunk(
    chunk: DocumentChunkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        embedding = get_embedding([chunk.content])[0]
        new_chunk = DocumentChunk(
            file_id=chunk.file_id,
            content=chunk.content,
            embedding=embedding,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index,
            created_at=datetime.utcnow()
        )
        db.add(new_chunk)
        db.commit()
        db.refresh(new_chunk)
        return new_chunk
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunks = db.query(DocumentChunk).all()
        return chunks
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
async def get_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
        return chunk
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{chunk_id}", response_model=DocumentChunkResponse)
async def update_document_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
        
        for key, value in chunk_update.dict(exclude_unset=True).items():
            setattr(chunk, key, value)
        
        db.commit()
        db.refresh(chunk)
        return chunk
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
        
        db.delete(chunk)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))