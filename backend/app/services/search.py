# app/services/search.py

from typing import Optional, List

from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.db.qdrant import client
from app.services.embedding import embed_query_text
from app.services.indexing import VECTOR_SIZE  # still 768

# Minimum similarity score threshold (cosine similarity, ranges from -1 to 1)
# Lower threshold = more results but potentially lower quality
# For CodeBERT embeddings, cosine similarity typically ranges from 0.7-0.99 for good matches
# Based on testing, most relevant results score 0.88-0.95, so 0.88 filters low-quality while keeping good matches
# Note: Set to None to disable threshold filtering
MIN_SCORE_THRESHOLD = 0.88  # Balanced threshold for quality results


def _normalize_query(query: str) -> str:
    """
    Normalize and clean the search query for better embedding quality.
    """
    # Strip whitespace
    query = query.strip()
    # Remove excessive whitespace
    query = " ".join(query.split())
    return query


def _normalize_filter_value(value: Optional[str]) -> Optional[str]:
    """
    Normalize filter values - treat empty strings as None.
    """
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def search_code(
    query: str,
    top_k: int = 5,
    repo_id: Optional[str] = None,
    language: Optional[str] = None,
    min_score: Optional[float] = None,
):
    """
    Search for code chunks using semantic similarity.
    
    Args:
        query: Natural language or code query string
        top_k: Maximum number of results to return
        repo_id: Optional repository filter (empty strings treated as None)
        language: Optional language filter (e.g., 'python', empty strings treated as None)
        min_score: Optional minimum similarity score threshold (defaults to MIN_SCORE_THRESHOLD, None to disable)
    
    Returns:
        List of search results with code chunks and metadata
    """
    # Normalize query
    query = _normalize_query(query)
    
    if not query:
        return []
    
    # Normalize filter values (handle empty strings)
    repo_id = _normalize_filter_value(repo_id)
    language = _normalize_filter_value(language)
    
    # Use default min_score if not provided (None means no threshold)
    if min_score is None:
        min_score = MIN_SCORE_THRESHOLD
    
    # Embed query using CodeBERT
    query_vec = embed_query_text(query)

    # Build optional filter (only add if values are not None/empty)
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

    try:
        # Use query_points with the vector query
        # query_points returns QueryResponse which has a 'points' field (List[ScoredPoint])
        query_params = {
            "collection_name": "code_chunks",
            "query": query_vec,
            "limit": top_k,
            "with_payload": True,
            "with_vectors": False,
        }
        
        # Add optional filters only if they exist
        if q_filter is not None:
            query_params["query_filter"] = q_filter
        
        # Add score threshold only if specified (None means no threshold in Qdrant)
        if min_score is not None:
            query_params["score_threshold"] = min_score
        
        response = client.query_points(**query_params)
    except Exception as e:
        # Log error with more details and return empty results
        print(f"Error during vector search: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return []

    results = []
    # Track seen results to avoid duplicates (based on file_path + start_line + symbol_name)
    seen_results = set()
    
    # QueryResponse.points is a List[ScoredPoint] (already sorted by score descending)
    for point in response.points:
        payload = point.payload or {}
        
        # Skip results with missing essential data
        if not payload.get("code"):
            continue
        
        # Create a unique key for deduplication
        result_key = (
            payload.get("file_path"),
            payload.get("start_line"),
            payload.get("symbol_name"),
        )
        
        # Skip duplicates
        if result_key in seen_results:
            continue
        seen_results.add(result_key)
        
        results.append(
            {
                "score": float(point.score),
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
