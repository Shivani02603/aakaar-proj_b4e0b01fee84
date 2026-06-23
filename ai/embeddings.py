import os
from typing import List
import openai

class EmbeddingClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        openai.api_key = self.api_key
        self.model = "text-embedding-3-small"

    def embed_text(self, text: str) -> List[float]:
        if not text:
            raise ValueError("Input text cannot be empty.")
        response = openai.Embedding.create(
            model=self.model,
            input=text
        )
        embedding = response['data'][0]['embedding']
        if len(embedding) != 1536:
            raise ValueError(f"Embedding dimension mismatch. Expected 1536, got {len(embedding)}.")
        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            raise ValueError("Input texts cannot be empty.")
        response = openai.Embedding.create(
            model=self.model,
            input=texts
        )
        embeddings = [item['embedding'] for item in response['data']]
        for embedding in embeddings:
            if len(embedding) != 1536:
                raise ValueError(f"Embedding dimension mismatch. Expected 1536, got {len(embedding)}.")
        return embeddings

def get_embedding(texts: List[str]) -> List[List[float]]:
    client = EmbeddingClient()
    return client.embed_batch(texts)