import os
from typing import Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from database.models import UploadedFile

UPLOAD_DIR = "uploads"

def save_file_to_disk(file, upload_dir=UPLOAD_DIR) -> str:
    """
    Save an uploaded file to disk.
    """
    try:
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return file_path
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file to disk: {str(e)}"
        )

def create_uploaded_file(file: Dict, db: Session) -> UploadedFile:
    """
    Create a new UploadedFile record in the database.
    """
    try:
        uploaded_file = UploadedFile(**file)
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        return uploaded_file
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create uploaded file record: {str(e)}"
        )

def get_uploaded_file_by_id(file_id: str, db: Session) -> UploadedFile:
    """
    Retrieve an UploadedFile record by ID.
    """
    try:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not file:
            raise HTTPException(
                status_code=404,
                detail="Uploaded file not found."
            )
        return file
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve uploaded file: {str(e)}"
        )

def list_uploaded_files(db: Session) -> list[UploadedFile]:
    """
    List all UploadedFile records.
    """
    try:
        return db.query(UploadedFile).all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list uploaded files: {str(e)}"
        )

def update_uploaded_file(file_id: str, update_data: Dict, db: Session) -> UploadedFile:
    """
    Update an UploadedFile record.
    """
    try:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not file:
            raise HTTPException(
                status_code=404,
                detail="Uploaded file not found."
            )
        for key, value in update_data.items():
            setattr(file, key, value)
        db.commit()
        db.refresh(file)
        return file
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update uploaded file: {str(e)}"
        )

def delete_uploaded_file(file_id: str, db: Session) -> bool:
    """
    Delete an UploadedFile record.
    """
    try:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not file:
            raise HTTPException(
                status_code=404,
                detail="Uploaded file not found."
            )
        db.delete(file)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete uploaded file: {str(e)}"
        )