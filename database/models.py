import os
import uuid
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Text,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    JSON,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, VECTOR
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

DATABASE_URL_ENV = "DATABASE_URL"
DATABASE_URL = os.environ[DATABASE_URL_ENV]

Base = declarative_base()

# Database engine and session setup
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    sessions = relationship("Session", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, created_at={self.created_at})>"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="sessions")
    uploaded_files = relationship("UploadedFile", back_populates="session")
    messages = relationship("Message", back_populates="session")

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, name={self.name}, created_at={self.created_at}, updated_at={self.updated_at})>"


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    processing_status = Column(String, nullable=False)

    session = relationship("Session", back_populates="uploaded_files")
    document_chunks = relationship("DocumentChunk", back_populates="uploaded_file")

    def __repr__(self):
        return f"<UploadedFile(id={self.id}, session_id={self.session_id}, filename={self.filename}, original_filename={self.original_filename}, file_size={self.file_size}, uploaded_at={self.uploaded_at}, processing_status={self.processing_status})>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(VECTOR(1536), nullable=False)
    metadata = Column(JSONB, nullable=True)
    sheet_name = Column(String, nullable=False)
    row_start = Column(Integer, nullable=False)
    row_end = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    uploaded_file = relationship("UploadedFile", back_populates="document_chunks")

    __table_args__ = (
        Index("ix_document_chunks_embedding", "embedding", postgresql_using="hnsw"),
    )

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, file_id={self.file_id}, sheet_name={self.sheet_name}, row_start={self.row_start}, row_end={self.row_end}, chunk_index={self.chunk_index}, created_at={self.created_at})>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    session = relationship("Session", back_populates="messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_role_valid"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, session_id={self.session_id}, role={self.role}, created_at={self.created_at})>"