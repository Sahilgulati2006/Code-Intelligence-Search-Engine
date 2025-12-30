from pydantic import BaseModel, HttpUrl
from typing import Optional


class IndexRequest(BaseModel):
    repo_url: HttpUrl


class IndexResponse(BaseModel):
    job_id: str
    status: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None
    indexed_chunks: Optional[int] = None
