import os
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from ai.embeddings import get_embedding
from ai.vector_store import vector_store
from ai.llm import gemini_flash_stream

app = FastAPI()

async def stream_answer(query: str, session_id: str, user_id: str):
    # Read API keys lazily
    openai_api_key = os.getenv("OPENAI_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not openai_api_key or not gemini_api_key:
        raise RuntimeError("API keys are not set in environment variables.")

    # Step 1: Embed the query
    query_embedding = get_embedding(query, api_key=openai_api_key)

    # Step 2: Retrieve top-5 chunks from vector store
    top_chunks = vector_store.search(query_embedding, top_k=5)

    # Step 3: Build the prompt with retrieved context
    context = "\n\n".join(chunk["content"] for chunk in top_chunks)
    prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"

    # Step 4: Call gemini-2.0-flash with stream=True
    async for token in gemini_flash_stream(prompt, api_key=gemini_api_key, stream=True):
        yield f'data: {{"token": "{token}"}}\n'

    # Step 5: After final token, yield done signal with citations
    citations = [chunk["source"] for chunk in top_chunks]
    yield f'data: {{"done": true, "citations": {citations}}}\n'

@app.get("/stream", response_class=StreamingResponse)
async def stream(query: str = Query(...), session_id: str = Query(...), user_id: str = Query(...)):
    return StreamingResponse(stream_answer(query, session_id, user_id), media_type="text/event-stream")