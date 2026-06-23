from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.services.auth import get_current_user
from ai.vector_store import VectorStore

router = APIRouter(
    prefix="/query pipeline - retrieval",
    tags=["Query Pipeline - Retrieval"]
)

# Pydantic Schemas
class DocumentChunkBase(BaseModel):
    content: str
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: Optional[int] = None

class DocumentChunkCreate(DocumentChunkBase):
    file_id: UUID

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[dict] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: Optional[int] = None

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    file_id: UUID
    created_at: str

class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5

class RetrievalResponse(BaseModel):
    chunks: List[DocumentChunkResponse]

# Dependency for JWT authentication
def jwt_auth(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    return get_current_user(credentials)

# Routes
@router.get("/", response_model=List[DocumentChunkResponse])
def list_chunks(db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).all()
    return [DocumentChunkResponse(
        id=chunk.id,
        file_id=chunk.file_id,
        content=chunk.content,
        metadata=chunk.metadata,
        sheet_name=chunk.sheet_name,
        row_start=chunk.row_start,
        row_end=chunk.row_end,
        chunk_index=chunk.chunk_index,
        created_at=chunk.created_at.isoformat()
    ) for chunk in chunks]

@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
def get_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
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

@router.post("/", response_model=DocumentChunkResponse)
def create_chunk(chunk_data: DocumentChunkCreate, db: Session = Depends(get_db)):
    chunk = DocumentChunk(**chunk_data.dict())
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
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

@router.put("/{chunk_id}", response_model=DocumentChunkResponse)
def update_chunk(chunk_id: UUID, chunk_data: DocumentChunkUpdate, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    for key, value in chunk_data.dict(exclude_unset=True).items():
        setattr(chunk, key, value)
    db.commit()
    db.refresh(chunk)
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

@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    db.delete(chunk)
    db.commit()
    return

@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_chunks(request: RetrievalRequest, db: Session = Depends(get_db), current_user: dict = Depends(jwt_auth)):
    vector_store = VectorStore()
    results = vector_store.search(request.query, top_k=request.top_k)
    chunks = []
    for result in results:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == result["id"]).first()
        if chunk:
            chunks.append(DocumentChunkResponse(
                id=chunk.id,
                file_id=chunk.file_id,
                content=chunk.content,
                metadata=chunk.metadata,
                sheet_name=chunk.sheet_name,
                row_start=chunk.row_start,
                row_end=chunk.row_end,
                chunk_index=chunk.chunk_index,
                created_at=chunk.created_at.isoformat()
            ))
    return RetrievalResponse(chunks=chunks)