from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from ai.embeddings import get_embedding

router = APIRouter(
    prefix="/query pipeline - query embedding",
    tags=["Query Pipeline - Query Embedding"]
)

# Pydantic Schemas
class QueryEmbeddingRequest(BaseModel):
    query: str = Field(..., description="The query text to embed.")
    session_id: UUID = Field(..., description="The session ID associated with the query.")

class QueryEmbeddingResponse(BaseModel):
    embedding: List[float] = Field(..., description="The embedding vector for the query.")
    session_id: UUID = Field(..., description="The session ID associated with the query.")

class DocumentChunkResponse(BaseModel):
    id: UUID = Field(..., description="The unique identifier of the document chunk.")
    content: str = Field(..., description="The content of the document chunk.")
    embedding: List[float] = Field(..., description="The embedding vector of the document chunk.")
    metadata: Dict = Field(..., description="Additional metadata for the document chunk.")
    sheet_name: Optional[str] = Field(None, description="The name of the sheet if applicable.")
    row_start: Optional[int] = Field(None, description="The starting row index of the chunk.")
    row_end: Optional[int] = Field(None, description="The ending row index of the chunk.")
    chunk_index: Optional[int] = Field(None, description="The index of the chunk.")

# Endpoint to embed a query
@router.post("/embed", response_model=QueryEmbeddingResponse, status_code=status.HTTP_200_OK)
async def embed_query(request: QueryEmbeddingRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Embed a query and return the embedding vector.
    """
    try:
        embedding = get_embedding([request.query])[0]
        return QueryEmbeddingResponse(embedding=embedding, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to embed query: {str(e)}")

# Endpoint to list all document chunks
@router.get("/chunks", response_model=List[DocumentChunkResponse], status_code=status.HTTP_200_OK)
async def list_document_chunks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    List all document chunks.
    """
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
                chunk_index=chunk.chunk_index
            )
            for chunk in chunks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list document chunks: {str(e)}")

# Endpoint to get a document chunk by ID
@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse, status_code=status.HTTP_200_OK)
async def get_document_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get a document chunk by ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Document chunk not found.")
        return DocumentChunkResponse(
            id=chunk.id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
            chunk_index=chunk.chunk_index
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document chunk: {str(e)}")

# Endpoint to create a document chunk
@router.post("/chunks", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
async def create_document_chunk(chunk: DocumentChunkResponse, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Create a new document chunk.
    """
    try:
        new_chunk = DocumentChunk(**chunk.dict())
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
            chunk_index=new_chunk.chunk_index
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document chunk: {str(e)}")

# Endpoint to update a document chunk by ID
@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse, status_code=status.HTTP_200_OK)
async def update_document_chunk(chunk_id: UUID, update_data: DocumentChunkResponse, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Update a document chunk by ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Document chunk not found.")
        for key, value in update_data.dict().items():
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
            chunk_index=chunk.chunk_index
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document chunk: {str(e)}")

# Endpoint to delete a document chunk by ID
@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_chunk(chunk_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Delete a document chunk by ID.
    """
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Document chunk not found.")
        db.delete(chunk)
        db.commit()
        return {"detail": "Document chunk deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document chunk: {str(e)}")