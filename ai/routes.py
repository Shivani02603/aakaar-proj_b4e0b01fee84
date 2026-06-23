from fastapi import APIRouter, Depends, UploadFile, Form, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from backend.services.auth import get_current_user
from ai.ingest import ingest_document
from ai.rag import answer_question
from ai.streaming import stream_answer

router = APIRouter(prefix='/api/ai')

class IngestRequest(BaseModel):
    session_id: Optional[str]

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str]

class QueryResponse(BaseModel):
    answer: str
    citations: list[str]

@router.post("/ingest")
async def ingest(file: UploadFile, session_id: Optional[str] = Form(None), current_user: dict = Depends(get_current_user)):
    """
    Endpoint to ingest an uploaded document.
    """
    await ingest_document(file, session_id, current_user['id'])
    return {"message": "Document ingested successfully"}

@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, current_user: dict = Depends(get_current_user)):
    """
    Endpoint to handle user queries and return answers with citations.
    """
    result = await answer_question(request.question, request.session_id or '', current_user['id'])
    return {"answer": result['answer'], "citations": result['sources']}

@router.get("/stream")
async def stream(query: str = Query(...), session_id: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    """
    Endpoint to stream answers for a given query.
    """
    return StreamingResponse(stream_answer(query, session_id or '', current_user['id']), media_type='text/event-stream')