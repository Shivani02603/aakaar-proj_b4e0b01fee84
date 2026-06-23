import uuid
from sqlalchemy.exc import SQLAlchemyError
from database.models import (
    engine,
    SessionLocal,
    User,
    Session,
    UploadedFile,
    DocumentChunk,
    Message
)

def seed_database():
    session = SessionLocal()
    try:
        # Seed Users
        user1 = User(
            id=uuid.uuid4(),
            email="user1@example.com",
            username="user1",
            password_hash="hashed_password_1",
            is_active=True
        )
        user2 = User(
            id=uuid.uuid4(),
            email="user2@example.com",
            username="user2",
            password_hash="hashed_password_2",
            is_active=True
        )
        user3 = User(
            id=uuid.uuid4(),
            email="user3@example.com",
            username="user3",
            password_hash="hashed_password_3",
            is_active=False
        )
        session.add_all([user1, user2, user3])
        session.commit()

        # Seed Sessions
        session1 = Session(
            id=uuid.uuid4(),
            user_id=user1.id,
            name="Session 1",
        )
        session2 = Session(
            id=uuid.uuid4(),
            user_id=user2.id,
            name="Session 2",
        )
        session3 = Session(
            id=uuid.uuid4(),
            user_id=user3.id,
            name="Session 3",
        )
        session.add_all([session1, session2, session3])
        session.commit()

        # Seed UploadedFiles
        file1 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session1.id,
            filename="file1.xlsx",
            original_filename="original_file1.xlsx",
            file_size=1024,
            processing_status="processed"
        )
        file2 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session2.id,
            filename="file2.xlsx",
            original_filename="original_file2.xlsx",
            file_size=2048,
            processing_status="processing"
        )
        file3 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session3.id,
            filename="file3.xlsx",
            original_filename="original_file3.xlsx",
            file_size=4096,
            processing_status="failed"
        )
        session.add_all([file1, file2, file3])
        session.commit()

        # Seed DocumentChunks
        chunk1 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file1.id,
            content="Chunk 1 content",
            embedding=[0.1] * 1536,
            metadata={"source": "file1"},
            sheet_name="Sheet1",
            row_start=1,
            row_end=10,
            chunk_index=0
        )
        chunk2 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file2.id,
            content="Chunk 2 content",
            embedding=[0.2] * 1536,
            metadata={"source": "file2"},
            sheet_name="Sheet2",
            row_start=11,
            row_end=20,
            chunk_index=1
        )
        chunk3 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file3.id,
            content="Chunk 3 content",
            embedding=[0.3] * 1536,
            metadata={"source": "file3"},
            sheet_name="Sheet3",
            row_start=21,
            row_end=30,
            chunk_index=2
        )
        session.add_all([chunk1, chunk2, chunk3])
        session.commit()

        # Seed Messages
        message1 = Message(
            id=uuid.uuid4(),
            session_id=session1.id,
            role="user",
            content="User message 1",
            citations={"source": "file1"}
        )
        message2 = Message(
            id=uuid.uuid4(),
            session_id=session2.id,
            role="assistant",
            content="Assistant message 2",
            citations={"source": "file2"}
        )
        message3 = Message(
            id=uuid.uuid4(),
            session_id=session3.id,
            role="system",
            content="System message 3",
            citations={"source": "file3"}
        )
        session.add_all([message1, message2, message3])
        session.commit()

        print("Database seeded successfully!")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()