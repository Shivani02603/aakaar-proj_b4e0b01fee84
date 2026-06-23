import os
from typing import List, Dict
from fastapi import HTTPException
from .embeddings import get_embedding
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from pgvector.sqlalchemy import Vector
from google.generativeai import generate_text

# Constants
TOP_K = 5

# Async retrieval function
async def retrieve_context(query: str, top_k: int, session_id: str, user_id: str) -> List[Dict]:
    # Read API keys lazily
    pg_url = os.getenv("POSTGRES_URL")
    if not pg_url:
        raise HTTPException(status_code=500, detail="POSTGRES_URL not set in environment variables")
    
    # Database setup
    engine = create_async_engine(pg_url)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Embed query
    query_embedding = get_embedding(query)

    # Retrieve top-k chunks
    async with async_session() as session:
        vector_table = Table(
            "vectors", MetaData(),
            Column("id", Integer, primary_key=True),
            Column("embedding", Vector(1536)),
            Column("metadata", String)
        )
        stmt = select(vector_table).order_by(vector_table.c.embedding.cosine_distance(query_embedding)).limit(top_k)
        result = await session.execute(stmt)
        rows = result.fetchall()

    return [{"embedding": row.embedding, "metadata": row.metadata} for row in rows]

# Async answer generation function
async def answer_question(query: str, session_id: str, user_id: str) -> Dict:
    # Retrieve context
    chunks = await retrieve_context(query, TOP_K, session_id, user_id)
    if not chunks:
        return {"answer": "No relevant information found.", "sources": []}

    # Build prompt
    context = "\n".join([chunk["metadata"] for chunk in chunks])
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"

    # Generate answer
    api_key = os.getenv("GOOGLE_GENERATIVEAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_GENERATIVEAI_API_KEY not set in environment variables")
    generate_text.configure(api_key=api_key)
    response = generate_text(prompt=prompt)

    # Build sources
    sources = [{"filename": chunk["metadata"]["source_filename"], "location": chunk["metadata"]["page_or_row"]} for chunk in chunks]

    return {"answer": response.text, "sources": sources}