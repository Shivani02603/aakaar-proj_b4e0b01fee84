from sqlalchemy.orm import Session
from uuid import UUID
from database.models import Session as DBSession, Message
from fastapi import HTTPException

def create_session(session, db: Session) -> DBSession:
    """
    Create a new session.
    """
    try:
        new_session = DBSession(**session.dict())
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )

def list_sessions(db: Session) -> list[DBSession]:
    """
    List all sessions.
    """
    try:
        return db.query(DBSession).all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )

def get_session_messages(session_id: UUID, db: Session) -> list[Message]:
    """
    Retrieve all messages for a specific session.
    """
    try:
        return db.query(Message).filter(Message.session_id == session_id).all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session messages: {str(e)}"
        )