from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import UploadedFile, Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(
    prefix="/frontend-citation-display",
    tags=["Frontend - Citation Display"]
)

# Pydantic schemas
class CitationBase(BaseModel):
    id: UUID
    message_id: UUID
    source: str
    created_at: Optional[str] = None

class CitationCreate(BaseModel):
    message_id: UUID
    source: str

class CitationUpdate(BaseModel):
    source: Optional[str]

class CitationResponse(CitationBase):
    pass

# CRUD endpoints
@router.get("/", response_model=List[CitationResponse])
def list_citations(db: Session = Depends(get_db)):
    citations = db.query(Message).all()
    return [CitationResponse(
        id=citation.id,
        message_id=citation.message_id,
        source=citation.source,
        created_at=citation.created_at.isoformat() if citation.created_at else None
    ) for citation in citations]

@router.get("/{citation_id}", response_model=CitationResponse)
def get_citation(citation_id: UUID, db: Session = Depends(get_db)):
    citation = db.query(Message).filter(Message.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    return CitationResponse(
        id=citation.id,
        message_id=citation.message_id,
        source=citation.source,
        created_at=citation.created_at.isoformat() if citation.created_at else None
    )

@router.post("/", response_model=CitationResponse)
def create_citation(citation: CitationCreate, db: Session = Depends(get_db)):
    new_citation = Message(
        message_id=citation.message_id,
        source=citation.source
    )
    db.add(new_citation)
    db.commit()
    db.refresh(new_citation)
    return CitationResponse(
        id=new_citation.id,
        message_id=new_citation.message_id,
        source=new_citation.source,
        created_at=new_citation.created_at.isoformat() if new_citation.created_at else None
    )

@router.put("/{citation_id}", response_model=CitationResponse)
def update_citation(citation_id: UUID, citation_update: CitationUpdate, db: Session = Depends(get_db)):
    citation = db.query(Message).filter(Message.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    if citation_update.source:
        citation.source = citation_update.source
    db.commit()
    db.refresh(citation)
    return CitationResponse(
        id=citation.id,
        message_id=citation.message_id,
        source=citation.source,
        created_at=citation.created_at.isoformat() if citation.created_at else None
    )

@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_citation(citation_id: UUID, db: Session = Depends(get_db)):
    citation = db.query(Message).filter(Message.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    db.delete(citation)
    db.commit()