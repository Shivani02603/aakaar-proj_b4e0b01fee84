import os
from typing import List, Dict
from fastapi import HTTPException
from tiktoken import get_encoding
from .embeddings import get_embedding
from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from python_docx import Document

# Lazy initialization of database connection
def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not set in environment variables")
    return create_async_engine(db_url)

async def chunk(document: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    enc = get_encoding("cl100k_base")
    tokens = enc.encode(document)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunks.append(enc.decode(tokens[start:end]))
        start += chunk_size - chunk_overlap
    return chunks

async def ingest_document(file_path: str, session_id: str, user_id: str):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File not found")

    document = Document(file_path)
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    full_text = "\n".join(paragraphs)

    chunks = await chunk(full_text)
    embeddings = [await get_embedding(chunk) for chunk in chunks]

    engine = get_db_engine()
    async with engine.begin() as conn:
        metadata = MetaData()
        vector_table = Table(
            "vectors",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("vector", Vector(1536)),
            Column("metadata", String),
        )
        metadata.create_all(conn)

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            metadata_dict = {
                "source_filename": os.path.basename(file_path),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "page_or_row": f"Paragraph {i + 1}",
            }
            stmt = insert(vector_table).values(
                vector=embedding,
                metadata=str(metadata_dict),
            )
            await conn.execute(stmt)