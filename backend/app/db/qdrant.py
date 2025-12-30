# app/db/qdrant.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

VECTOR_SIZE = 768  # CodeBERT dimension size

client = QdrantClient(url="http://localhost:6333")

def init_collection(reset: bool = False):
    """
    Ensure the Qdrant collection for code chunks exists.
    If `reset` is True, the collection will be recreated (clearing existing data).
    """
    try:
        # Check if collection exists
        client.get_collection(collection_name="code_chunks")
        if reset:
            client.recreate_collection(
                collection_name="code_chunks",
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                ),
            )
            print("Qdrant collection 'code_chunks' recreated.")
        else:
            print("Qdrant collection 'code_chunks' already exists.")
    except Exception:
        # Collection not found — create it
        client.recreate_collection(
            collection_name="code_chunks",
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            ),
        )
        print("Qdrant collection 'code_chunks' initialized.")
