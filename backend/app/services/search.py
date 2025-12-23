# app/services/search.py

from typing import List
import numpy as np

from app.db.qdrant import client
from app.services.indexing import VECTOR_SIZE


def embed_query_dummy(text: str) -> List[float]:
    return np.random.rand(VECTOR_SIZE).astype("float32").tolist()


def search_code(query: str, top_k: int = 5, repo_id=None, language=None):
    query_vec = embed_query_dummy(query)

    hits = client.search(
        collection_name="code_chunks",
        query_vector=query_vec,
        limit=top_k,
    )

    results = []
    for h in hits:
        payload = h.payload or {}
        results.append(
            {
                "score": h.score,
                "repo_id": payload.get("repo_id"),
                "file_path": payload.get("file_path"),
                "language": payload.get("language"),
                "symbol_type": payload.get("symbol_type"),
                "symbol_name": payload.get("symbol_name"),
                "start_line": payload.get("start_line"),
                "end_line": payload.get("end_line"),
                "code": payload.get("code"),
            }
        )

    return results
