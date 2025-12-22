# app/services/indexing.py

from typing import List, Dict, Any
import uuid

import numpy as np
from qdrant_client.models import PointStruct

from app.db.qdrant import client


VECTOR_SIZE = 768  # must match qdrant VECTOR_SIZE


def embed_code_dummy(texts: List[str]) -> List[List[float]]:
    """
    Temporary dummy embedding function.
    Later we'll replace this with a real CodeBERT-based embedding.
    """
    return np.random.rand(len(texts), VECTOR_SIZE).astype("float32").tolist()


def index_chunks(chunks: List[Dict[str, Any]], repo_id: str):
    """
    Take parsed code chunks and index them into Qdrant.
    """
    texts = [c["code"] for c in chunks]
    vectors = embed_code_dummy(texts)

    points = []
    for chunk, vec in zip(chunks, vectors):
        points.append(
            PointStruct(
                id=int(uuid.uuid4().int % (2**63 - 1)),
                vector=vec,
                payload={
                    **chunk,
                    "repo_id": repo_id,
                },
            )
        )

    client.upsert(
        collection_name="code_chunks",
        points=points,
    )
    print(f"Indexed {len(points)} chunks into Qdrant.")
