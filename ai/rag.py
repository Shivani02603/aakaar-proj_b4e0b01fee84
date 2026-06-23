import os
from typing import List, Dict
from fastapi import HTTPException
from .embeddings import get_embedding
from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from google.generativeai import generate_text

# Lazy initialization of database connection
def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not set in environment variables")
    return create_async_engine(db_url)

async def retrieve_context(query: str, top_k: int, session_id: str, user_id: str) -> List[Dict]:
    query_embedding = await get_embedding(query)
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

        stmt = vector_table.select().order_by(Vector.cosine_similarity(query_embedding)).limit(top_k)
        result = await conn.execute(stmt)
        rows = result.fetchall()

    return [{"vector": row.vector, "metadata": row.metadata} for row in rows]

async def answer_question(query: str, session_id: str, user_id: str) -> Dict:
    context_chunks = await retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
    if not context_chunks:
        return {"answer": "No relevant information found.", "sources": []}

    context = "\n".join([chunk["metadata"] for chunk in context_chunks])
    sources = [{"filename": chunk["metadata"]["source_filename"], "location": chunk["metadata"]["page_or_row"]} for chunk in context_chunks]

    api_key = os.getenv("GOOGLE_GENERATIVEAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_GENERATIVEAI_API_KEY not set in environment variables")

    response = generate_text(api_key=api_key, prompt=f"Context: {context}\n\nQuestion: {query}\n\nAnswer:")
    answer = response.get("text", "").strip()

    return {"answer": answer, "sources": sources}