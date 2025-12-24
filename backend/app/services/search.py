# app/services/search.py

from typing import Optional, List

from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.db.qdrant import client
from app.services.embedding import embed_query_text
from app.services.indexing import VECTOR_SIZE  # still 768


def search_code(
    query: str,
    top_k: int = 5,
    repo_id: Optional[str] = None,
    language: Optional[str] = None,
):
    # Embed query using CodeBERT
    query_vec = embed_query_text(query)

    # Build optional filter
    q_filter: Optional[Filter] = None
    conditions: List[FieldCondition] = []

    if repo_id:
        conditions.append(
            FieldCondition(
                key="repo_id",
                match=MatchValue(value=repo_id),
            )
        )

    if language:
        conditions.append(
            FieldCondition(
                key="language",
                match=MatchValue(value=language),
            )
        )

    if conditions:
        q_filter = Filter(must=conditions)

    hits = client.search(
        collection_name="code_chunks",
        query_vector=query_vec,
        limit=top_k,
        query_filter=q_filter,
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
