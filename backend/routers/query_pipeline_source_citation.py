from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import SourceCitation
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(
    prefix="/query pipeline - source citation",
    tags=["Query Pipeline - Source Citation"]
)

# Pydantic Schemas
class SourceCitationBase(BaseModel):
    filename: str = Field(..., description="Name of the file containing the citation")
    row_start: int = Field(..., description="Starting row of the citation")
    row_end: int = Field(..., description="Ending row of the citation")

class SourceCitationCreate(SourceCitationBase):
    pass

class SourceCitationUpdate(BaseModel):
    filename: Optional[str] = Field(None, description="Updated name of the file containing the citation")
    row_start: Optional[int] = Field(None, description="Updated starting row of the citation")
    row_end: Optional[int] = Field(None, description="Updated ending row of the citation")

class SourceCitationResponse(SourceCitationBase):
    id: UUID = Field(..., description="Unique identifier for the citation")

# CRUD Endpoints
@router.post("/", response_model=SourceCitationResponse, status_code=status.HTTP_201_CREATED)
def create_citation(citation: SourceCitationCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_citation = SourceCitation(**citation.dict())
    db.add(new_citation)
    db.commit()
    db.refresh(new_citation)
    return new_citation

@router.get("/", response_model=List[SourceCitationResponse], status_code=status.HTTP_200_OK)
def list_citations(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citations = db.query(SourceCitation).all()
    return citations

@router.get("/{citation_id}", response_model=SourceCitationResponse, status_code=status.HTTP_200_OK)
def get_citation(citation_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citation = db.query(SourceCitation).filter(SourceCitation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    return citation

@router.put("/{citation_id}", response_model=SourceCitationResponse, status_code=status.HTTP_200_OK)
def update_citation(citation_id: UUID, citation_update: SourceCitationUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citation = db.query(SourceCitation).filter(SourceCitation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    for key, value in citation_update.dict(exclude_unset=True).items():
        setattr(citation, key, value)
    db.commit()
    db.refresh(citation)
    return citation

@router.delete("/{citation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_citation(citation_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    citation = db.query(SourceCitation).filter(SourceCitation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    db.delete(citation)
    db.commit()
    return None

# Functional Requirement Endpoint
@router.post("/answer", response_model=List[SourceCitationResponse], status_code=status.HTTP_200_OK)
def get_answer_with_citations(query: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Placeholder logic for retrieving citations based on the query
    # Replace with actual implementation for query processing and citation retrieval
    citations = db.query(SourceCitation).filter(SourceCitation.filename.ilike(f"%{query}%")).all()
    if not citations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No citations found for the query")
    return citations