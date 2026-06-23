from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from database.models import DocumentChunk, UploadedFile
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(
    prefix="/ingestion_pipeline_parsing",
    tags=["Ingestion Pipeline - Parsing"]
)

# Pydantic schemas for request and response
class DocumentChunkBase(BaseModel):
    file_id: UUID
    content: str
    metadata: dict
    sheet_name: str
    row_start: int
    row_end: int
    chunk_index: int
    created_at: datetime

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID

class UploadedFileResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: datetime
    processing_status: str

# Endpoint to parse an uploaded Excel file
@router.post("/parse_excel", response_model=List[DocumentChunkResponse], status_code=status.HTTP_201_CREATED)
async def parse_excel_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Parse an uploaded Excel file and create document chunks.
    """
    try:
        # Save the uploaded file to disk temporarily
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Read the Excel file using pandas
        excel_data = pd.ExcelFile(file_path)
        chunks = []

        for sheet_name in excel_data.sheet_names:
            sheet_data = excel_data.parse(sheet_name)
            for index, row in sheet_data.iterrows():
                chunk = DocumentChunk(
                    file_id=None,  # Placeholder, should be linked to the actual file
                    content=row.to_json(),
                    metadata={"sheet_name": sheet_name},
                    sheet_name=sheet_name,
                    row_start=index,
                    row_end=index,
                    chunk_index=index,
                    created_at=datetime.utcnow()
                )
                db.add(chunk)
                db.commit()
                db.refresh(chunk)
                chunks.append(chunk)

        return [DocumentChunkResponse.from_orm(chunk) for chunk in chunks]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing Excel file: {str(e)}"
        )

    finally:
        # Clean up the temporary file
        import os
        if os.path.exists(file_path):
            os.remove(file_path)

# CRUD endpoints for DocumentChunk
@router.get("/chunks", response_model=List[DocumentChunkResponse])
def list_chunks(db: Session = Depends(get_db)):
    """
    List all document chunks.
    """
    chunks = db.query(DocumentChunk).all()
    return [DocumentChunkResponse.from_orm(chunk) for chunk in chunks]

@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
def get_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific document chunk by ID.
    """
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found"
        )
    return DocumentChunkResponse.from_orm(chunk)

@router.post("/chunks", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
def create_chunk(chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    """
    Create a new document chunk.
    """
    new_chunk = DocumentChunk(**chunk.dict())
    db.add(new_chunk)
    db.commit()
    db.refresh(new_chunk)
    return DocumentChunkResponse.from_orm(new_chunk)

@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
def update_chunk(chunk_id: UUID, chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    """
    Update an existing document chunk.
    """
    existing_chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not existing_chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found"
        )
    for key, value in chunk.dict().items():
        setattr(existing_chunk, key, value)
    db.commit()
    db.refresh(existing_chunk)
    return DocumentChunkResponse.from_orm(existing_chunk)

@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a document chunk.
    """
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found"
        )
    db.delete(chunk)
    db.commit()
    return {"detail": "Document chunk deleted successfully"}