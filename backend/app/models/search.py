# app/models/search.py

from typing import Optional, List
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    repo_id: Optional[str] = None
    language: Optional[str] = None


class SearchResultItem(BaseModel):
    score: float
    repo_id: Optional[str] = None
    file_path: Optional[str] = None
    language: Optional[str] = None
    symbol_type: Optional[str] = None
    symbol_name: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    code: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
