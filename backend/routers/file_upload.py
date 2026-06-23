from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import UploadedFile
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.file_service import save_file_to_disk, create_uploaded_file, get_uploaded_file_by_id, list_uploaded_files, update_uploaded_file, delete_uploaded_file

router = APIRouter(prefix="/file-upload", tags=["File Upload"])

# Pydantic schemas
class UploadedFileBase(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: datetime
    processing_status: str

class UploadedFileCreate(BaseModel):
    session_id: UUID
    filename: str
    original_filename: str
    file_size: int

class UploadedFileResponse(UploadedFileBase):
    id: UUID

class UploadedFileUpdate(BaseModel):
    processing_status: Optional[str] = None

# Routes
@router.post("/", response_model=UploadedFileResponse)
async def upload_file(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # Save file to disk
        file_path = save_file_to_disk(file, upload_dir="uploads/")
        file_size = len(file.file.read())
        
        # Create UploadedFile record
        uploaded_file = UploadedFileCreate(
            session_id=session_id,
            filename=file_path,
            original_filename=file.filename,
            file_size=file_size,
        )
        created_file = create_uploaded_file(uploaded_file, db)
        return UploadedFileResponse(**created_file.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[UploadedFileResponse])
async def list_files(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        files = list_uploaded_files(db)
        return [UploadedFileResponse(**file.__dict__) for file in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}", response_model=UploadedFileResponse)
async def get_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        file = get_uploaded_file_by_id(file_id, db)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return UploadedFileResponse(**file.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{file_id}", response_model=UploadedFileResponse)
async def update_file(
    file_id: UUID,
    update_data: UploadedFileUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        updated_file = update_uploaded_file(file_id, update_data.dict(exclude_unset=True), db)
        if not updated_file:
            raise HTTPException(status_code=404, detail="File not found")
        return UploadedFileResponse(**updated_file.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        deleted = delete_uploaded_file(file_id, db)
        if not deleted:
            raise HTTPException(status_code=404, detail="File not found")
        return {"detail": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))