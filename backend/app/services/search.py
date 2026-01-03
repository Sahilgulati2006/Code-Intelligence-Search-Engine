# app/services/search.py

import os
from typing import Optional, List, Dict, Any, Tuple, Set
from collections import Counter
import math

from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.db.qdrant import client
from app.services.embedding import embed_query_text, embed_code_chunks
from app.services.indexing import VECTOR_SIZE  # still 768

# Tuning parameters (can be overridden via environment variables)
MIN_SCORE_THRESHOLD = None
TEXT_VEC_WEIGHT = float(os.getenv("SEARCH_TEXT_VEC_WEIGHT", "0.4"))
CODE_VEC_WEIGHT = float(os.getenv("SEARCH_CODE_VEC_WEIGHT", "0.2"))
LEXICAL_WEIGHT = float(os.getenv("SEARCH_LEXICAL_WEIGHT", "0.3"))
BM25_WEIGHT = float(os.getenv("SEARCH_BM25_WEIGHT", "0.1"))
DOCSTRING_BOOST = float(os.getenv("SEARCH_DOCSTRING_BOOST", "0.15"))
FUNCTION_BOOST = float(os.getenv("SEARCH_FUNCTION_BOOST", "0.10"))
SIGNATURE_MATCH_BOOST = float(os.getenv("SEARCH_SIGNATURE_MATCH_BOOST", "0.12"))
FETCH_MULTIPLIER = int(os.getenv("SEARCH_FETCH_MULTIPLIER", "12"))
FETCH_MIN = int(os.getenv("SEARCH_FETCH_MIN", "30"))
FETCH_MAX = int(os.getenv("SEARCH_FETCH_MAX", "300"))

# Semantic synonyms for better matching (query term -> code-related terms)
SEMANTIC_SYNONYMS = {
    "duplicate": ["repetition", "repeated", "duplicate", "duplication", "repetitions"],
    "remove": ["delete", "strip", "filter", "remove", "eliminate"],
    "unique": ["distinct", "unique", "set", "deduplicate"],
    "empty": ["empty", "blank", "null", "none", "clear"],
    "sort": ["sort", "sorted", "order", "arrange"],
    "filter": ["filter", "select", "where", "match"],
    "loop": ["for", "while", "iterate", "loop", "iteration"],
    "check": ["validate", "verify", "check", "assert", "test"],
    "convert": ["convert", "transform", "parse", "encode", "decode"],
    "send": ["post", "request", "submit", "send", "transmit"],
    "get": ["get", "fetch", "retrieve", "load", "read"],
    "create": ["create", "new", "init", "build", "construct"],
    "split": ["split", "divide", "chunk", "partition"],
    "join": ["join", "concat", "merge", "combine"],
    "sentiment": ["sentiment", "emotion", "bias", "analysis", "feeling", "tone"],
    "extract": ["extract", "parse", "fetch", "retrieve", "pull"],
    "article": ["article", "text", "content", "document", "page"],
    "analyze": ["analyze", "check", "examine", "process", "test"],
    "validate": ["validate", "verify", "check", "test", "assert"],
    "input": ["input", "parameter", "argument", "data", "field"],
}


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


def _expand_query_semantically(query: str) -> List[str]:
    """
    Expand query with semantic synonyms to improve recall. Returns a list of query variations.
    E.g., "remove duplicates" -> [\"remove duplicates\", "delete unique", "filter repetition", ...]
    """
    q_lower = query.lower()
    tokens = set(q_lower.split())
    expansions = [query]
    
    # Find which tokens have semantic synonyms
    synonym_map = {}
    for base_term, synonyms in SEMANTIC_SYNONYMS.items():
        for syn in synonyms:
            if syn in tokens or syn in q_lower:
                synonym_map[syn] = base_term
    
    # Generate expansions by swapping synonyms
    if synonym_map:
        # Try up to 4 expansions with different synonym combinations
        items = list(synonym_map.items())
        for i in range(min(len(items), 4)):
            syn, base = items[i]
            alt_tokens = tokens.copy()
            # Remove the current synonym if it's a token
            if syn in alt_tokens:
                alt_tokens.discard(syn)
            # Add other synonyms for the same base term
            other_syns = [s for s in SEMANTIC_SYNONYMS[base] if s != syn and s not in alt_tokens]
            if other_syns:
                alt_tokens.add(other_syns[0])
                expansions.append(" ".join(sorted(alt_tokens)))
    
    # Also add the original query with common expansions (function -> functions, etc.)
    if tokens:
        first_token = list(tokens)[0]
        if not first_token.endswith('s'):
            expansions.append(query + "s")
    
    return expansions[:5]  # Return up to 5 query variations


def _bm25_score(query: str, payload: Dict[str, Any]) -> float:
    """
    Compute a BM25-inspired lexical score. This rewards:
    - Term frequency in short fields (symbol_name, docstring) more
    - Presence of all query terms
    - Exact phrase matches
    """
    if not query:
        return 0.0
    
    q_tokens = set([t.lower() for t in query.split() if len(t) > 1])
    if not q_tokens:
        return 0.0
    
    # BM25 parameters
    k1, b = 1.5, 0.75
    
    def field_score(field: Optional[str], field_length_norm: float = 1.0) -> float:
        if not field:
            return 0.0
        field_l = field.lower()
        tokens = [t for t in field_l.split() if len(t) > 1]
        freq = Counter(tokens)
        
        # Term frequency component
        score = 0.0
        for q_token in q_tokens:
            if q_token in freq:
                tf = freq[q_token]
                score += (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * field_length_norm))
        
        # Bonus for phrase matching (if multiple query tokens appear consecutively)
        if len(q_tokens) > 1 and " ".join(sorted(q_tokens)) in field_l:
            score += 0.5
        
        return score
    
    # Weight different fields (signature/docstring heavily, code moderately, symbol name heavily)
    s_sig = field_score(payload.get("signature"), 0.5) * 2.5
    s_doc = field_score(payload.get("docstring"), 0.7) * 1.5
    s_symbol = field_score(payload.get("symbol_name"), 0.3) * 3.0
    s_code = field_score(payload.get("code"), 2.0) * 0.8
    
    total = s_sig + s_doc + s_symbol + s_code
    # Normalize to [0, 1] range
    return min(1.0, total / max(1.0, max(s_sig, s_doc, s_symbol, s_code) * 2))


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


def _looks_like_code(text: str) -> bool:
    """
    Heuristic to decide if a query is code-like. If true, we embed using the code embedding model
    which can improve precision for code snippet queries.
    """
    if "\n" in text:
        return True
    code_indicators = ["def ", "class ", "{", "}", "->", "=>", "();", "()", "import ", "from ", "#include", "//"]
    text_lower = text.lower()
    for tok in code_indicators:
        if tok in text_lower:
            return True
    return False


def _signature_semantic_match(query: str, signature: Optional[str]) -> float:
    """
    Compute semantic similarity between query and function signature.
    E.g., query "remove duplicates" should match signature "remove_repetitions(text)".
    Also match based on docstring hints in combined context.
    """
    if not signature or not query:
        return 0.0
    
    sig_lower = signature.lower()
    q_lower = query.lower()
    
    # Extract function name from signature
    if "(" in sig_lower:
        func_name = sig_lower.split("(")[0].strip()
    else:
        func_name = sig_lower
    
    # Check if query tokens appear in function name (handle underscores/camelCase)
    q_tokens = set([t for t in q_lower.split() if len(t) > 1])
    sig_tokens = set(func_name.replace("_", " ").replace("-", " ").split())
    
    if q_tokens & sig_tokens:
        overlap = len(q_tokens & sig_tokens) / float(len(q_tokens | sig_tokens))
        # Strong match if ANY query token is in the function name
        if overlap > 0:
            return min(1.0, overlap + 0.3)  # boost for any match
    
    return 0.0


def _lexical_score(query: str, payload: Dict[str, Any]) -> float:
    """
    Compute a comprehensive lexical match score in [0,1] using multiple text fields
    and incorporating semantic context (docstring, signature, etc).
    """
    if not query:
        return 0.0
    
    q = query.lower().strip()
    q_tokens = set([t for t in q.split() if len(t) > 1])
    if not q_tokens:
        return 0.0

    def overlap(text: Optional[str], field_weight: float = 1.0) -> float:
        if not text:
            return 0.0
        text_l = text.lower()
        # Exact substring match -> very strong signal
        if q in text_l:
            return 1.0 * field_weight
        # Partial phrase match (2+ consecutive tokens)
        if len(q_tokens) > 1:
            phrase = " ".join(sorted(list(q_tokens)[:2]))
            if phrase in text_l:
                return 0.9 * field_weight
        tokens = set([t for t in text_l.replace('/', ' ').replace('_', ' ').replace('-', ' ').split() if len(t) > 1])
        if not tokens:
            return 0.0
        jaccard = len(q_tokens & tokens) / float(len(q_tokens | tokens))
        return jaccard * field_weight

    s_symbol = overlap(payload.get("symbol_name"), 1.3)  # symbol name is strong indicator
    s_context = overlap(payload.get("semantic_context"), 1.2)  # context/docstring is important
    s_doc = overlap(payload.get("docstring"), 1.1)
    s_code = overlap(payload.get("code"), 0.8)  # code snippets can be verbose
    s_file = overlap(payload.get("file_path"), 0.4)
    s_repo = overlap(payload.get("repo_id"), 0.15)

    return max(s_symbol, s_context, s_doc, s_code, s_file, s_repo)


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

    # Expand query with semantic synonyms for better recall
    query_variations = _expand_query_semantically(query)
    
    # Embed query with both text and code embedders
    text_vecs = [embed_query_text(qv) for qv in query_variations]
    code_vecs = [embed_code_chunks([qv])[0] for qv in query_variations]

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

    # Fetch candidates using multiple query variations for better coverage
    try:
        fetch_limit = min(max(top_k * FETCH_MULTIPLIER, FETCH_MIN), FETCH_MAX)

        candidates_map: Dict[Tuple, Dict[str, Any]] = {}

        # Query with all text and code vectors
        for text_vec in text_vecs:
            params = {
                "collection_name": "code_chunks",
                "query": text_vec,
                "limit": fetch_limit,
                "with_payload": True,
                "with_vectors": False,
            }
            if q_filter is not None:
                params["query_filter"] = q_filter
            if min_score is not None:
                params["score_threshold"] = min_score * 0.8  # Relax threshold for initial fetch
            
            resp = client.query_points(**params)
            for point in resp.points:
                payload = point.payload or {}
                if not payload.get("code"):
                    continue
                key = (payload.get("file_path"), payload.get("start_line"), payload.get("symbol_name"))
                if key not in candidates_map:
                    candidates_map[key] = {"payload": payload, "text_scores": [], "code_scores": []}
                candidates_map[key]["text_scores"].append(float(point.score) if point.score is not None else 0.0)

        for code_vec in code_vecs:
            params = {
                "collection_name": "code_chunks",
                "query": code_vec,
                "limit": fetch_limit,
                "with_payload": True,
                "with_vectors": False,
            }
            if q_filter is not None:
                params["query_filter"] = q_filter
            if min_score is not None:
                params["score_threshold"] = min_score * 0.8
            
            resp = client.query_points(**params)
            for point in resp.points:
                payload = point.payload or {}
                if not payload.get("code"):
                    continue
                key = (payload.get("file_path"), payload.get("start_line"), payload.get("symbol_name"))
                if key not in candidates_map:
                    candidates_map[key] = {"payload": payload, "text_scores": [], "code_scores": []}
                candidates_map[key]["code_scores"].append(float(point.score) if point.score is not None else 0.0)

    except Exception as e:
        print(f"Error during vector search: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return []

    # Re-rank candidates with multi-signal scoring
    scored = []
    for key, entry in candidates_map.items():
        payload = entry["payload"]
        
        # Take max scores from multiple vectors
        t_score = max(entry.get("text_scores", [0.0])) if entry.get("text_scores") else 0.0
        c_score = max(entry.get("code_scores", [0.0])) if entry.get("code_scores") else 0.0
        
        # Lexical and BM25 scores
        lex_score = _lexical_score(query, payload)
        bm25_score = _bm25_score(query, payload)
        sig_match = _signature_semantic_match(query, payload.get("signature"))

        # Adaptive weighting: code queries favor code vector, NL queries favor text
        if _looks_like_code(query):
            w_code = CODE_VEC_WEIGHT + 0.1
            w_text = max(0.0, TEXT_VEC_WEIGHT - 0.1)
        else:
            w_code = CODE_VEC_WEIGHT
            w_text = TEXT_VEC_WEIGHT

        # Normalize weights
        total_w = w_text + w_code + LEXICAL_WEIGHT + BM25_WEIGHT
        w_text /= total_w
        w_code /= total_w
        w_lex = LEXICAL_WEIGHT / total_w
        w_bm25 = BM25_WEIGHT / total_w

        combined = w_text * t_score + w_code * c_score + w_lex * lex_score + w_bm25 * bm25_score

        # Add signature semantic match boost (now with higher weight)
        if sig_match > 0.3:
            combined = min(1.0, combined + SIGNATURE_MATCH_BOOST * sig_match * 1.5)

        # Docstring/document boost
        if payload.get("symbol_type") in ("doc", "docstring"):
            if lex_score > 0.0:
                combined = min(1.0, combined + DOCSTRING_BOOST)

        # Prefer function definitions even more strongly, and penalize call-only chunks
        if payload.get("symbol_type") == "function":
            combined = min(1.0, combined + FUNCTION_BOOST + 0.05)  # extra boost for functions
        elif payload.get("symbol_type") == "call":
            combined = max(0.0, combined - 0.05)  # slight penalty for call-sites

        scored.append((combined, t_score, c_score, lex_score, bm25_score, sig_match, key, payload))

    # Sort and return top_k
    scored.sort(key=lambda t: t[0], reverse=True)

    results = []
    seen_results = set()
    for combined, t_score, c_score, lex_score, bm25_score, sig_match, key, payload in scored:
        if key in seen_results:
            continue
        seen_results.add(key)

        if min_score is not None and combined < min_score:
            continue

        results.append({
            "score": float(combined),
            "repo_id": payload.get("repo_id"),
            "file_path": payload.get("file_path"),
            "language": payload.get("language"),
            "symbol_type": payload.get("symbol_type"),
            "symbol_name": payload.get("symbol_name"),
            "start_line": payload.get("start_line"),
            "end_line": payload.get("end_line"),
            "code": payload.get("code"),
        })

        if len(results) >= top_k:
            break

    return results


def search_similar_code(
    code: str,
    top_k: int = 5,
    repo_id: Optional[str] = None,
    language: Optional[str] = None,
    exclude_self: bool = True,
    min_score: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Find code chunks similar to the given code snippet using vector similarity.
    This enables code-to-code search (finding duplicate/similar code patterns).

    Improvements: perform larger candidate fetch and re-rank using lexical features and function boosts.
    """
    # Normalize code
    code = code.strip()

    if not code:
        return []

    # Normalize filter values (handle empty strings)
    repo_id = _normalize_filter_value(repo_id)
    language = _normalize_filter_value(language)

    # Use default min_score if not provided (None means no threshold)
    if min_score is None:
        min_score = MIN_SCORE_THRESHOLD

    # Always use code embedder here (we're comparing code snippets)
    code_vec = embed_code_chunks([code])[0]

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
        fetch_limit = min(max(top_k * FETCH_MULTIPLIER, FETCH_MIN), FETCH_MAX)
        query_params = {
            "collection_name": "code_chunks",
            "query": code_vec,
            "limit": fetch_limit,
            "with_payload": True,
            "with_vectors": False,
        }

        if q_filter is not None:
            query_params["query_filter"] = q_filter

        if min_score is not None:
            query_params["score_threshold"] = min_score

        response = client.query_points(**query_params)
    except Exception as e:
        print(f"Error during similar code search: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return []

    candidates_map: Dict[Tuple, Dict[str, Any]] = {}
    for point in response.points:
        payload = point.payload or {}
        if not payload.get("code"):
            continue

        # Optionally exclude exact matches
        if exclude_self:
            payload_code = payload.get("code", "").strip()
            if payload_code == code.strip():
                continue

        key = (payload.get("file_path"), payload.get("start_line"), payload.get("symbol_name"))
        entry = candidates_map.get(key, {"payload": payload, "code_score": 0.0})
        entry["code_score"] = max(entry.get("code_score", 0.0), float(point.score) if point.score is not None else 0.0)
        candidates_map[key] = entry

    scored = []
    for key, entry in candidates_map.items():
        payload = entry["payload"]
        c_score = entry.get("code_score", 0.0)
        lex_score = _lexical_score(code, payload)

        # We give slightly more weight to vector similarity for code-to-code search
        total_w = (CODE_VEC_WEIGHT + LEXICAL_WEIGHT)
        w_code = CODE_VEC_WEIGHT / total_w
        w_lex = LEXICAL_WEIGHT / total_w

        combined = w_code * c_score + w_lex * lex_score

        if payload.get("symbol_type") == "function":
            combined = min(1.0, combined + FUNCTION_BOOST)

        scored.append((combined, c_score, lex_score, key, payload))

    scored.sort(key=lambda t: t[0], reverse=True)

    results = []
    seen_results = set()
    for combined, c_score, lex_score, key, payload in scored:
        if key in seen_results:
            continue
        seen_results.add(key)

        if min_score is not None and combined < min_score:
            continue

        results.append({
            "score": float(combined),
            "repo_id": payload.get("repo_id"),
            "file_path": payload.get("file_path"),
            "language": payload.get("language"),
            "symbol_type": payload.get("symbol_type"),
            "symbol_name": payload.get("symbol_name"),
            "start_line": payload.get("start_line"),
            "end_line": payload.get("end_line"),
            "code": payload.get("code"),
        })

        if len(results) >= top_k:
            break

    return results
