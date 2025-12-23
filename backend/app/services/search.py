# app/services/search.py

from typing import List
from app.db.qdrant import client
from app.services.embedding import embed_query_text
from app.services.indexing import VECTOR_SIZE  # still 768


def search_code(query: str, top_k: int = 5, repo_id=None, language=None):
    # REAL embedding for query
    query_vec = embed_query_text(query)

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
