import pandas as pd
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk
from datetime import datetime


class ParsingService:
    async def parse_excel_file(file_path: str, session_id: UUID, db: AsyncSession) -> List[DocumentChunk]:
        """
        Parses an Excel file and creates document chunks for each sheet.
        """
        try:
            # Load the Excel file
            excel_data = pd.ExcelFile(file_path)
            chunks = []

            for sheet_name in excel_data.sheet_names:
                sheet_data = excel_data.parse(sheet_name)

                if sheet_data.empty:
                    continue

                for index, row in sheet_data.iterrows():
                    chunk = DocumentChunk(
                        file_id=session_id,
                        content=row.to_json(),
                        metadata={"sheet_name": sheet_name},
                        sheet_name=sheet_name,
                        row_start=index,
                        row_end=index,
                        chunk_index=index,
                        created_at=datetime.utcnow(),
                    )
                    chunks.append(chunk)

            # Save chunks to the database
            db.add_all(chunks)
            await db.commit()
            return chunks
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found.")
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="Excel file is empty or invalid.")
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    async def create_chunk(chunk_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Creates a single document chunk in the database.
        """
        try:
            chunk = DocumentChunk(**chunk_data)
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_chunk_by_id(chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        """
        Retrieves a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found.")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def list_all_chunks(db: AsyncSession) -> List[DocumentChunk]:
        """
        Lists all document chunks in the database.
        """
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update_chunk(chunk_id: UUID, update_data: dict, db: AsyncSession) -> DocumentChunk:
        """
        Updates a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found.")

            for key, value in update_data.items():
                setattr(chunk, key, value)

            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def delete_chunk(chunk_id: UUID, db: AsyncSession) -> None:
        """
        Deletes a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Chunk not found.")

            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")