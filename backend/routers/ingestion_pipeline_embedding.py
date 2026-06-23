from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ai.embeddings import get_embedding

router = APIRouter(
    prefix="/ingestion_pipeline_embedding",
    tags=["Ingestion Pipeline - Embedding"]
)

# Pydantic schemas
class DocumentChunkBase(BaseModel):
    content: str
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: Optional[int] = None

class DocumentChunkCreate(DocumentChunkBase):
    file_id: UUID

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    embedding: List[float]
    created_at: str

class DocumentChunkUpdate(BaseModel):
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: Optional[int] = None

# Dependency for JWT authentication
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    # Placeholder for actual JWT validation logic
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return {"user_id": "example_user_id"}  # Replace with actual user extraction logic

# Routes
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
        )
        db.add(new_chunk)
        db.commit()
        db.refresh(new_chunk)
        return DocumentChunkResponse(
            id=new_chunk.id,
            content=new_chunk.content,
            embedding=new_chunk.embedding,
            metadata=new_chunk.metadata,
            sheet_name=new_chunk.sheet_name,
            row_start=new_chunk.row_start,
            row_end=new_chunk.row_end,
            chunk_index=new_chunk.chunk_index,
            created_at=new_chunk.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        chunks = db.query(DocumentChunk).all()
        return [
            DocumentChunkResponse(
                id=chunk.id,
                content=chunk.content,
                embedding=chunk.embedding,
                metadata=chunk.metadata,
                sheet_name=chunk.sheet_name,
                row_start=chunk.row_start,
                row_end=chunk.row_end,
                chunk_index=chunk.chunk_index,
                created_at=chunk.created_at.isoformat(),
            )
            for chunk in chunks
        ]
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
        return DocumentChunkResponse(
            id=chunk.id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at.isoformat(),
        )
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
        return DocumentChunkResponse(
            id=chunk.id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at.isoformat(),
        )
    except Exception as e:
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))