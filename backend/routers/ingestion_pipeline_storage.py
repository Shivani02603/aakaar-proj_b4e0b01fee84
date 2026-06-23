from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(
    prefix="/ingestion-pipeline-storage",
    tags=["Ingestion Pipeline - Storage"]
)

# Pydantic schemas
class DocumentChunkBase(BaseModel):
    file_id: UUID
    content: str
    embedding: List[float]
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: Optional[int] = None

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: Optional[int] = None

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: str

# Dependency for JWT authentication
def jwt_auth(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    # Placeholder for actual JWT validation logic
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return credentials

# Routes
@router.post("/", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
async def create_document_chunk(
    chunk: DocumentChunkCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(jwt_auth)
):
    try:
        new_chunk = DocumentChunk(**chunk.dict())
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
    credentials: HTTPAuthorizationCredentials = Depends(jwt_auth)
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
    credentials: HTTPAuthorizationCredentials = Depends(jwt_auth)
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
    credentials: HTTPAuthorizationCredentials = Depends(jwt_auth)
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
    credentials: HTTPAuthorizationCredentials = Depends(jwt_auth)
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