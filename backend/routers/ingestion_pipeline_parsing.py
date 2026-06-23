from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import pandas as pd
import io
import logging
from sqlalchemy.orm import Session
from database.models import UploadedFile, DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix='/ingestion_pipeline_parsing', tags=['Ingestion Pipeline - Parsing'])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Pydantic schemas
class DocumentChunkBase(BaseModel):
    file_id: UUID
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: int

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    chunk_index: Optional[int] = None

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Helper function to parse Excel file
async def parse_excel_file(file: UploadFile, db: Session, current_user: Any) -> List[DocumentChunkResponse]:
    try:
        # Read file content
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
        
        # Use pandas to read Excel file
        excel_data = pd.ExcelFile(io.BytesIO(contents))
        chunks = []
        chunk_index = 0
        
        for sheet_name in excel_data.sheet_names:
            try:
                sheet_data = pd.read_excel(excel_data, sheet_name=sheet_name)
                if sheet_data.empty:
                    logger.warning(f"Sheet '{sheet_name}' is empty, skipping")
                    continue
                
                # Convert sheet to string representation
                sheet_content = sheet_data.to_string(index=False)
                if not sheet_content.strip():
                    continue
                
                # Create chunk for entire sheet
                chunk_data = DocumentChunkCreate(
                    file_id=UUID(file.filename),  # This should be actual file ID from database
                    content=sheet_content,
                    metadata={"sheet_name": sheet_name, "columns": list(sheet_data.columns)},
                    sheet_name=sheet_name,
                    row_start=0,
                    row_end=len(sheet_data) - 1,
                    chunk_index=chunk_index
                )
                
                # Save to database
                db_chunk = DocumentChunk(
                    id=UUID(int=chunk_index),
                    file_id=chunk_data.file_id,
                    content=chunk_data.content,
                    metadata=chunk_data.metadata,
                    sheet_name=chunk_data.sheet_name,
                    row_start=chunk_data.row_start,
                    row_end=chunk_data.row_end,
                    chunk_index=chunk_data.chunk_index,
                    created_at=datetime.utcnow()
                )
                db.add(db_chunk)
                db.commit()
                db.refresh(db_chunk)
                
                chunks.append(DocumentChunkResponse.from_orm(db_chunk))
                chunk_index += 1
                
            except Exception as sheet_error:
                logger.error(f"Error processing sheet '{sheet_name}': {str(sheet_error)}")
                continue
        
        if not chunks:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid data found in Excel file")
        
        return chunks
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Excel file contains no data")
    except pd.errors.ParserError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Excel file format")
    except Exception as e:
        logger.error(f"Error parsing Excel file: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to parse Excel file: {str(e)}")

# Endpoints
@router.post("/parse_excel", response_model=List[DocumentChunkResponse])
async def parse_excel_endpoint(
    file: UploadFile = File(...),
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Parse an uploaded Excel file and create document chunks for each sheet.
    """
    current_user = await get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an Excel file (.xlsx or .xls)")
    
    return await parse_excel_file(file, db, current_user)

@router.get("/chunks", response_model=List[DocumentChunkResponse])
async def list_chunks(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all document chunks with pagination.
    """
    current_user = await get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    chunks = db.query(DocumentChunk).offset(skip).limit(limit).all()
    return [DocumentChunkResponse.from_orm(chunk) for chunk in chunks]

@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_chunk(
    chunk_id: UUID,
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get a specific document chunk by ID.
    """
    current_user = await get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    
    return DocumentChunkResponse.from_orm(chunk)

@router.post("/chunks", response_model=DocumentChunkResponse)
async def create_chunk(
    chunk_data: DocumentChunkCreate,
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Create a new document chunk.
    """
    current_user = await get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    # Check if file exists
    file = db.query(UploadedFile).filter(UploadedFile.id == chunk_data.file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found")
    
    db_chunk = DocumentChunk(
        id=UUID(int=len(db.query(DocumentChunk).all()) + 1),
        file_id=chunk_data.file_id,
        content=chunk_data.content,
        metadata=chunk_data.metadata,
        sheet_name=chunk_data.sheet_name,
        row_start=chunk_data.row_start,
        row_end=chunk_data.row_end,
        chunk_index=chunk_data.chunk_index,
        created_at=datetime.utcnow()
    )
    
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    
    return DocumentChunkResponse.from_orm(db_chunk)

@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def update_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkUpdate,
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Update an existing document chunk.
    """
    current_user = await get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    
    update_data = chunk_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chunk, field, value)
    
    db.commit()
    db.refresh(chunk)
    
    return DocumentChunkResponse.from_orm(chunk)

@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chunk(
    chunk_id: UUID,
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Delete a document chunk.
    """
    current_user = await get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    
    db.delete(chunk)
    db.commit()
    
    return None