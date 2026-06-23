from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import SourceCitation
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(
    prefix="/frontend-citation-display",
    tags=["Frontend - Citation Display"]
)

# Pydantic Schemas
class CitationBase(BaseModel):
    source: str = Field(..., example="https://example.com")
    description: Optional[str] = Field(None, example="Example citation description")

class CitationCreate(CitationBase):
    pass

class CitationUpdate(CitationBase):
    pass

class CitationResponse(CitationBase):
    id: UUID
    created_at: str

# Create Citation
@router.post("/", response_model=CitationResponse, status_code=status.HTTP_201_CREATED)
def create_citation(citation: CitationCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_citation = SourceCitation(**citation.dict())
    db.add(new_citation)
    db.commit()
    db.refresh(new_citation)
    return CitationResponse(
        id=new_citation.id,
        source=new_citation.source,
        description=new_citation.description,
        created_at=new_citation.created_at.isoformat()
    )

# Get Citation by ID
@router.get("/{citation_id}", response_model=CitationResponse, status_code=status.HTTP_200_OK)
def get_citation(citation_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citation = db.query(SourceCitation).filter(SourceCitation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    return CitationResponse(
        id=citation.id,
        source=citation.source,
        description=citation.description,
        created_at=citation.created_at.isoformat()
    )

# List Citations
@router.get("/", response_model=List[CitationResponse], status_code=status.HTTP_200_OK)
def list_citations(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citations = db.query(SourceCitation).all()
    return [
        CitationResponse(
            id=citation.id,
            source=citation.source,
            description=citation.description,
            created_at=citation.created_at.isoformat()
        )
        for citation in citations
    ]

# Update Citation
@router.put("/{citation_id}", response_model=CitationResponse, status_code=status.HTTP_200_OK)
def update_citation(citation_id: UUID, citation_update: CitationUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citation = db.query(SourceCitation).filter(SourceCitation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    for key, value in citation_update.dict(exclude_unset=True).items():
        setattr(citation, key, value)
    db.commit()
    db.refresh(citation)
    return CitationResponse(
        id=citation.id,
        source=citation.source,
        description=citation.description,
        created_at=citation.created_at.isoformat()
    )

# Delete Citation
@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_citation(citation_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citation = db.query(SourceCitation).filter(SourceCitation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    db.delete(citation)
    db.commit()
    return None