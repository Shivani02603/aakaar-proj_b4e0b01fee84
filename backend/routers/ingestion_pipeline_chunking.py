from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.ingestion_pipeline_chunking_service import ChunkingService

router = APIRouter(
    prefix="/ingestion-pipeline-chunking",
    tags=["Ingestion Pipeline - Chunking"]
)

# Pydantic schemas
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

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: str

# Routes
@router.post("/", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
async def create_chunk(
    chunk_data: DocumentChunkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunk = ChunkingService.create_chunk(chunk_data, db)
        return DocumentChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            content=chunk.content,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DocumentChunkResponse])
async def list_chunks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunks = ChunkingService.list_chunks(db)
        return [
            DocumentChunkResponse(
                id=chunk.id,
                file_id=chunk.file_id,
                content=chunk.content,
                metadata=chunk.metadata,
                sheet_name=chunk.sheet_name,
                row_start=chunk.row_start,
                row_end=chunk.row_end,
                chunk_index=chunk.chunk_index,
                created_at=chunk.created_at.isoformat()
            )
            for chunk in chunks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
async def get_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunk = ChunkingService.get_chunk_by_id(chunk_id, db)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return DocumentChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            content=chunk.content,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{chunk_id}", response_model=DocumentChunkResponse)
async def update_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunk = ChunkingService.update_chunk(chunk_id, chunk_update, db)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return DocumentChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            content=chunk.content,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        success = ChunkingService.delete_chunk(chunk_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Chunk not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))