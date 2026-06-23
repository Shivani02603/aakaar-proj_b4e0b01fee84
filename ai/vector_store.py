import os
from typing import List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class VectorStoreModel(Base):
    __tablename__ = "vector_store"
    id = Column(String, primary_key=True)
    vector = Column(Vector(1536), nullable=False)
    metadata = Column(JSON, nullable=True)

class VectorStore:
    def __init__(self):
        self._engine = None
        self._Session = None

    def _init_db(self):
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set.")
        self._engine = create_engine(db_url)
        self._Session = sessionmaker(bind=self._engine)
        Base.metadata.create_all(self._engine)

    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]):
        if not self._engine or not self._Session:
            self._init_db()
        session = self._Session()
        try:
            existing_entry = session.query(VectorStoreModel).filter_by(id=id).first()
            if existing_entry:
                existing_entry.vector = vector
                existing_entry.metadata = metadata
            else:
                new_entry = VectorStoreModel(id=id, vector=vector, metadata=metadata)
                session.add(new_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def search(self, query_embedding: List[float], top_k: int, **filters) -> List[Dict[str, Any]]:
        if not self._engine or not self._Session:
            self._init_db()
        session = self._Session()
        try:
            query = session.query(
                VectorStoreModel.id,
                VectorStoreModel.vector,
                VectorStoreModel.metadata
            ).order_by(VectorStoreModel.vector.cosine_distance(query_embedding)).limit(top_k)

            for key, value in filters.items():
                query = query.filter(VectorStoreModel.metadata[key] == value)

            results = query.all()
            matches = [
                {"id": result.id, "vector": result.vector, "metadata": result.metadata}
                for result in results
            ]
            return matches
        except Exception as e:
            raise e
        finally:
            session.close()

vector_store = VectorStore()