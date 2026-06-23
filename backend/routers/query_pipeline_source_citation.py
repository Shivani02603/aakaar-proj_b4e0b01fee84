from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import UploadedFile, DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from datetime import datetime

router = APIRouter(
    prefix="/query-pipeline-source-citation",
    tags=["Query Pipeline - Source Citation"]
)

# Pydantic Schemas
class SourceCitationBase(BaseModel):
    filename: str
    row_start: int
    row_end: int

class SourceCitationCreate(SourceCitationBase):
    pass

class SourceCitationResponse(SourceCitationBase):
    id: UUID
    created_at: datetime

class DocumentChunkResponse(BaseModel):
    id: UUID
    content: str
    embedding: Optional[List[float]]
    metadata: Optional[dict]
    sheet_name: Optional[str]
    row_start: int
    row_end: int
    chunk_index: int
    created_at: datetime

# CRUD Endpoints
@router.get("/", response_model=List[SourceCitationResponse])
def list_source_citations(db: Session = Depends(get_db)):
    try:
        citations = db.query(DocumentChunk).all()
        return [
            SourceCitationResponse(
                id=citation.id,
                filename=citation.metadata.get("filename", ""),
                row_start=citation.row_start,
                row_end=citation.row_end,
                created_at=citation.created_at
            )
            for citation in citations
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving source citations: {str(e)}"
        )

@router.get("/{citation_id}", response_model=SourceCitationResponse)
def get_source_citation(citation_id: UUID, db: Session = Depends(get_db)):
    try:
        citation = db.query(DocumentChunk).filter(DocumentChunk.id == citation_id).first()
        if not citation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source citation not found"
            )
        return SourceCitationResponse(
            id=citation.id,
            filename=citation.metadata.get("filename", ""),
            row_start=citation.row_start,
            row_end=citation.row_end,
            created_at=citation.created_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving source citation: {str(e)}"
        )

@router.post("/", response_model=SourceCitationResponse)
def create_source_citation(citation: SourceCitationCreate, db: Session = Depends(get_db)):
    try:
        new_citation = DocumentChunk(
            metadata={"filename": citation.filename},
            row_start=citation.row_start,
            row_end=citation.row_end,
            created_at=datetime.utcnow()
        )
        db.add(new_citation)
        db.commit()
        db.refresh(new_citation)
        return SourceCitationResponse(
            id=new_citation.id,
            filename=new_citation.metadata.get("filename", ""),
            row_start=new_citation.row_start,
            row_end=new_citation.row_end,
            created_at=new_citation.created_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating source citation: {str(e)}"
        )

@router.put("/{citation_id}", response_model=SourceCitationResponse)
def update_source_citation(citation_id: UUID, citation: SourceCitationCreate, db: Session = Depends(get_db)):
    try:
        existing_citation = db.query(DocumentChunk).filter(DocumentChunk.id == citation_id).first()
        if not existing_citation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source citation not found"
            )
        existing_citation.metadata["filename"] = citation.filename
        existing_citation.row_start = citation.row_start
        existing_citation.row_end = citation.row_end
        db.commit()
        db.refresh(existing_citation)
        return SourceCitationResponse(
            id=existing_citation.id,
            filename=existing_citation.metadata.get("filename", ""),
            row_start=existing_citation.row_start,
            row_end=existing_citation.row_end,
            created_at=existing_citation.created_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating source citation: {str(e)}"
        )

@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source_citation(citation_id: UUID, db: Session = Depends(get_db)):
    try:
        existing_citation = db.query(DocumentChunk).filter(DocumentChunk.id == citation_id).first()
        if not existing_citation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source citation not found"
            )
        db.delete(existing_citation)
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting source citation: {str(e)}"
        )

# Additional Endpoint for Answer with Source Citations
@router.post("/answer-with-citations", response_model=List[DocumentChunkResponse])
def get_answer_with_citations(query: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        # Simulate retrieval logic (replace with actual implementation)
        chunks = db.query(DocumentChunk).filter(DocumentChunk.content.ilike(f"%{query}%")).all()
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
                created_at=chunk.created_at
            )
            for chunk in chunks
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving answer with citations: {str(e)}"
        )