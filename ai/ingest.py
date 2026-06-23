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
from sqlalchemy.future import select
from python_docx import Document

# Constants
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Tokenizer setup
def count_tokens(text: str) -> int:
    enc = get_encoding("cl100k_base")
    return len(enc.encode(text))

# Chunking function
def chunk(document: str) -> List[Dict]:
    tokens = document.split()
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunks.append(" ".join(tokens[start:end]))
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

# Async ingestion function
async def ingest_document(file_path: str, session_id: str, user_id: str):
    # Read API keys lazily
    pg_url = os.getenv("POSTGRES_URL")
    if not pg_url:
        raise HTTPException(status_code=500, detail="POSTGRES_URL not set in environment variables")
    
    # Database setup
    engine = create_async_engine(pg_url)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Read document
    try:
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        document_text = "\n".join(paragraphs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading document: {str(e)}")

    # Chunking
    chunks = chunk(document_text)
    metadata = [{'source_filename': os.path.basename(file_path), 'chunk_index': i, 'total_chunks': len(chunks), 'page_or_row': f"Paragraph {i+1}"} for i in range(len(chunks))]

    # Embedding and upserting
    async with async_session() as session:
        for i, chunk_text in enumerate(chunks):
            embedding = get_embedding(chunk_text)
            vector_table = Table(
                "vectors", MetaData(),
                Column("id", Integer, primary_key=True),
                Column("embedding", Vector(1536)),
                Column("metadata", String)
            )
            stmt = insert(vector_table).values(
                embedding=embedding,
                metadata=metadata[i]
            ).on_conflict_do_update(
                index_elements=["id"],
                set_={"embedding": embedding, "metadata": metadata[i]}
            )
            await session.execute(stmt)
        await session.commit()