from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from ai.embeddings import get_embedding

router = APIRouter(
    prefix="/query_pipeline_query_embedding",
    tags=["Query Pipeline - Query Embedding"]
)

# Pydantic schemas
class QueryEmbeddingRequest(BaseModel):
    query: str = Field(..., description="The query text to embed")
    session_id: UUID = Field(..., description="Session ID associated with the query")

class QueryEmbeddingResponse(BaseModel):
    embedding: List[float] = Field(..., description="The embedding vector for the query")
    session_id: UUID = Field(..., description="Session ID associated with the query")

class DocumentChunkResponse(BaseModel):
    id: UUID = Field(..., description="Document chunk ID")
    file_id: UUID = Field(..., description="File ID associated with the chunk")
    content: str = Field(..., description="Content of the document chunk")
    embedding: List[float] = Field(..., description="Embedding vector of the chunk")
    metadata: dict = Field(..., description="Metadata of the chunk")
    sheet_name: Optional[str] = Field(None, description="Sheet name if applicable")
    row_start: Optional[int] = Field(None, description="Start row of the chunk")
    row_end: Optional[int] = Field(None, description="End row of the chunk")
    chunk_index: int = Field(..., description="Index of the chunk")
    created_at: str = Field(..., description="Timestamp of chunk creation")

# Endpoint to embed a query
@router.post("/embed", response_model=QueryEmbeddingResponse, status_code=status.HTTP_200_OK)
async def embed_query(
    request: QueryEmbeddingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Embed a query and return the embedding vector.
    """
    try:
        embedding = get_embedding([request.query])[0]  # Generate embedding for the query
        return QueryEmbeddingResponse(
            embedding=embedding,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to embed query: {str(e)}"
        )

# Endpoint to list all document chunks
@router.get("/chunks", response_model=List[DocumentChunkResponse], status_code=status.HTTP_200_OK)
def list_document_chunks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all document chunks.
    """
    try:
        chunks = db.query(DocumentChunk).all()
        return [
            DocumentChunkResponse(
                id=chunk.id,
                file_id=chunk.file_id,
                content=chunk.content,
                embedding=chunk.embedding,
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list document chunks: {str(e)}"
        )

# Endpoint to get a document chunk by ID
@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse, status_code=status.HTTP_200_OK)
def get_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a document chunk by ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document chunk not found"
            )
        return DocumentChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document chunk: {str(e)}"
        )

# Endpoint to delete a document chunk by ID
@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a document chunk by ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document chunk not found"
            )
        db.delete(chunk)
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document chunk: {str(e)}"
        )

# Endpoint to update a document chunk by ID
class DocumentChunkUpdateRequest(BaseModel):
    content: Optional[str] = Field(None, description="Updated content of the document chunk")
    metadata: Optional[dict] = Field(None, description="Updated metadata of the chunk")
    sheet_name: Optional[str] = Field(None, description="Updated sheet name if applicable")
    row_start: Optional[int] = Field(None, description="Updated start row of the chunk")
    row_end: Optional[int] = Field(None, description="Updated end row of the chunk")

@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse, status_code=status.HTTP_200_OK)
def update_document_chunk(
    chunk_id: UUID,
    update_data: DocumentChunkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a document chunk by ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document chunk not found"
            )
        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(chunk, key, value)
        db.commit()
        db.refresh(chunk)
        return DocumentChunkResponse(
            id=chunk.id,
            file_id=chunk.file_id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document chunk: {str(e)}"
        )