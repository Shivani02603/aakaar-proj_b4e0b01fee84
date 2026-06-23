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
    vector = Column(Vector(1536))
    metadata = Column(JSON)

class VectorStore:
    def __init__(self):
        self._engine = None
        self._Session = None

    def _get_engine(self):
        if not self._engine:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is not set.")
            self._engine = create_engine(db_url)
        return self._engine

    def _get_session(self):
        if not self._Session:
            engine = self._get_engine()
            self._Session = sessionmaker(bind=engine)
        return self._Session()

    def initialize(self):
        engine = self._get_engine()
        Base.metadata.create_all(engine)

    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]):
        if len(vector) != 1536:
            raise ValueError(f"Vector dimension mismatch. Expected 1536, got {len(vector)}.")
        session = self._get_session()
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
        if len(query_embedding) != 1536:
            raise ValueError(f"Query embedding dimension mismatch. Expected 1536, got {len(query_embedding)}.")
        session = self._get_session()
        try:
            query = session.query(VectorStoreModel)
            for key, value in filters.items():
                query = query.filter(VectorStoreModel.metadata[key] == value)
            results = query.order_by(VectorStoreModel.vector.cosine_distance(query_embedding)).limit(top_k).all()
            return [{"id": result.id, "metadata": result.metadata} for result in results]
        except Exception as e:
            raise e
        finally:
            session.close()

vector_store = VectorStore()