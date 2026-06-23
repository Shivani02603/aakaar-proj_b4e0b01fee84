from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import User, Session as DBSession, UploadedFile, DocumentChunk, Message
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/database", tags=["Database"])

# Pydantic Schemas
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    created_at: str

class UserUpdate(BaseModel):
    email: Optional[str]

class SessionBase(BaseModel):
    name: str

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: UUID
    user_id: UUID
    created_at: str
    updated_at: str

class SessionUpdate(BaseModel):
    name: Optional[str]

class UploadedFileBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    processing_status: str

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileResponse(UploadedFileBase):
    id: UUID
    session_id: UUID
    uploaded_at: str

class UploadedFileUpdate(BaseModel):
    processing_status: Optional[str]

class DocumentChunkBase(BaseModel):
    content: str
    metadata: dict
    sheet_name: str
    row_start: int
    row_end: int
    chunk_index: int

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    file_id: UUID
    created_at: str

class DocumentChunkUpdate(BaseModel):
    metadata: Optional[dict]

class MessageBase(BaseModel):
    role: str
    content: str
    citations: dict

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: UUID
    session_id: UUID
    created_at: str

class MessageUpdate(BaseModel):
    content: Optional[str]
    citations: Optional[dict]

# CRUD Endpoints for User
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_update.email:
        user.email = user_update.email
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()

# CRUD Endpoints for Session
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_session = DBSession(name=session.name, user_id=current_user.id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(DBSession).filter(DBSession.user_id == current_user.id).all()

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: UUID, session_update: SessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_update.name:
        session.name = session_update.name
    db.commit()
    db.refresh(session)
    return session

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(DBSession).filter(DBSession.id == session_id, DBSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()

# CRUD Endpoints for UploadedFile
@router.post("/files", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
def create_uploaded_file(file: UploadedFileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_file = UploadedFile(**file.dict(), session_id=current_user.id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("/files", response_model=List[UploadedFileResponse])
def list_uploaded_files(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(UploadedFile).filter(UploadedFile.session_id == current_user.id).all()

@router.get("/files/{file_id}", response_model=UploadedFileResponse)
def get_uploaded_file(file_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.session_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file

@router.put("/files/{file_id}", response_model=UploadedFileResponse)
def update_uploaded_file(file_id: UUID, file_update: UploadedFileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.session_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if file_update.processing_status:
        file.processing_status = file_update.processing_status
    db.commit()
    db.refresh(file)
    return file

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uploaded_file(file_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id, UploadedFile.session_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    db.delete(file)
    db.commit()

# CRUD Endpoints for DocumentChunk
@router.post("/chunks", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
def create_document_chunk(chunk: DocumentChunkCreate, db: Session = Depends(get_db)):
    db_chunk = DocumentChunk(**chunk.dict())
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

@router.get("/chunks", response_model=List[DocumentChunkResponse])
def list_document_chunks(db: Session = Depends(get_db)):
    return db.query(DocumentChunk).all()

@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
def get_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    return chunk

@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
def update_document_chunk(chunk_id: UUID, chunk_update: DocumentChunkUpdate, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    if chunk_update.metadata:
        chunk.metadata = chunk_update.metadata
    db.commit()
    db.refresh(chunk)
    return chunk

@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_chunk(chunk_id: UUID, db: Session = Depends(get_db)):
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")
    db.delete(chunk)
    db.commit()

# CRUD Endpoints for Message
@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_message = Message(**message.dict(), session_id=current_user.id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@router.get("/messages", response_model=List[MessageResponse])
def list_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Message).filter(Message.session_id == current_user.id).all()

@router.get("/messages/{message_id}", response_model=MessageResponse)
def get_message(message_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id, Message.session_id == current_user.id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message

@router.put("/messages/{message_id}", response_model=MessageResponse)
def update_message(message_id: UUID, message_update: MessageUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id, Message.session_id == current_user.id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message_update.content:
        message.content = message_update.content
    if message_update.citations:
        message.citations = message_update.citations
    db.commit()
    db.refresh(message)
    return message

@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id, Message.session_id == current_user.id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    db.delete(message)
    db.commit()