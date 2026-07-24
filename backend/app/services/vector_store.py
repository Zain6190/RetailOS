from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

from backend.app.core.config import settings

COLLECTION_NAME = "smartstore_documents"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # 384-dim, local, no API key needed


class VectorStore:
    _client: Optional[QdrantClient] = None
    _embedder: Optional[TextEmbedding] = None

    @classmethod
    def get_client(cls) -> QdrantClient:
        if cls._client is None:
            cls._client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY or None,
            )
        return cls._client

    @classmethod
    def get_embedder(cls) -> TextEmbedding:
        if cls._embedder is None:
            # First call downloads model weights (~130MB) once, then caches locally
            cls._embedder = TextEmbedding(model_name=EMBEDDING_MODEL)
        return cls._embedder

    @classmethod
    def ensure_collection(cls):
        client = cls.get_client()
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    @classmethod
    def embed_text(cls, text: str) -> List[float]:
        embedder = cls.get_embedder()
        return list(embedder.embed([text]))[0].tolist()

    @classmethod
    def upsert_document(cls, doc_id: int, title: str, content: str):
        cls.ensure_collection()
        client = cls.get_client()
        vector = cls.embed_text(f"{title}\n{content}")
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload={"title": title, "content": content},
                )
            ],
        )

    @classmethod
    def search(cls, query: str, top_k: int = 3) -> List[dict]:
        cls.ensure_collection()
        client = cls.get_client()
        query_vector = cls.embed_text(query)
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
        )
        return [
            {"title": r.payload.get("title"), "content": r.payload.get("content"), "score": r.score}
            for r in results.points
        ]