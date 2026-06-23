from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import UploadedFile
from database.config import get_db
from backend.services.file_service import save_file_to_disk, create_uploaded_file, get_uploaded_file_by_id, list_uploaded_files, update_uploaded_file, delete_uploaded_file

router = APIRouter()

# Pydantic schemas
class UploadedFileBase(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: datetime
    processing_status: str

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileResponse(UploadedFileBase):
    id: UUID

class UploadedFileUpdate(BaseModel):
    processing_status: Optional[str] = Field(None, description="Updated processing status of the file")

# Routes
@router.post("/upload", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload an Excel file (.xlsx) and save its metadata to the database.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are allowed for upload."
        )

    try:
        # Save file to disk
        file_path = save_file_to_disk(file, upload_dir="uploads")

        # Create file metadata in the database
        uploaded_file = create_uploaded_file(
            file={
                "session_id": session_id,
                "filename": file_path,
                "original_filename": file.filename,
                "file_size": len(await file.read()),
                "uploaded_at": datetime.utcnow(),
                "processing_status": "Pending",
            },
            db=db,
        )
        return uploaded_file
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

@router.get("/{file_id}/status", response_model=UploadedFileResponse)
def get_file_status(file_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve the processing status of a specific uploaded file by ID.
    """
    try:
        file = get_uploaded_file_by_id(file_id=file_id, db=db)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found."
            )
        return file
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file status: {str(e)}"
        )