# app/db/qdrant.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

VECTOR_SIZE = 768  # CodeBERT dimension size

client = QdrantClient(url="http://localhost:6333")

def init_collection():
    """
    Creates or resets the Qdrant collection for code chunks.
    Call this once before indexing.
    """
    client.recreate_collection(
        collection_name="code_chunks",
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        ),
    )
    print("Qdrant collection 'code_chunks' initialized.")
