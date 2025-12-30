# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.search import SearchRequest, SearchResponse, SimilarSearchRequest
from app.models.indexing import IndexRequest, IndexResponse, JobStatus
from app.services.search import search_code, search_similar_code
from app.services.parsing import extract_code_chunks
from app.services.indexing import index_chunks

from fastapi import BackgroundTasks, HTTPException
from typing import Dict, Any
import uuid
import tempfile
import shutil
import subprocess
import os
from urllib.parse import urlparse

app = FastAPI(title="Code Intelligence Backend")

# Simple in-memory job tracker. For production, use persistent store (Redis/DB/Queue).
JOBS: Dict[str, Dict[str, Any]] = {}

# Allow frontend dev server to call the API
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search_endpoint(body: SearchRequest):
    results = search_code(
        query=body.query,
        top_k=body.top_k,
        repo_id=body.repo_id,
        language=body.language,
    )
    return SearchResponse(results=results)


@app.post("/search/similar", response_model=SearchResponse)
def search_similar_endpoint(body: SimilarSearchRequest):
    """
    Find code chunks similar to the provided code snippet.
    This enables code-to-code search for finding duplicate/similar code patterns.
    """
    results = search_similar_code(
        code=body.code,
        top_k=body.top_k,
        repo_id=body.repo_id,
        language=body.language,
        exclude_self=body.exclude_self,
        min_score=body.min_score,
    )
    return SearchResponse(results=results)


def _is_valid_github_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http"):
            return False
        host = parsed.netloc.lower()
        if not host.endswith("github.com"):
            return False
        # path should be /owner/repo or /owner/repo.git
        parts = [p for p in parsed.path.split("/") if p]
        return len(parts) >= 2
    except Exception:
        return False


def _owner_repo_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    owner = parts[0]
    repo = parts[1]
    if repo.endswith('.git'):
        repo = repo[:-4]
    return f"{owner}/{repo}"


def _start_index_job(job_id: str, repo_url: str):
    JOBS[job_id]["status"] = "running"
    JOBS[job_id]["message"] = "Cloning repository"
    temp_dir = tempfile.mkdtemp(prefix="index_repo_")

    try:
        # Ensure git is available
        if shutil.which("git") is None:
            raise RuntimeError("'git' not found in PATH; cannot clone repositories")

        # Clone shallowly
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True, capture_output=True, text=True)
        JOBS[job_id]["message"] = "Extracting code chunks"
        chunks = extract_code_chunks(temp_dir)
        JOBS[job_id]["message"] = f"Indexing {len(chunks)} chunks"
        index_chunks(chunks, repo_id=_owner_repo_from_url(repo_url))
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["indexed_chunks"] = len(chunks)
        JOBS[job_id]["message"] = "Indexing complete"
    except subprocess.CalledProcessError as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["message"] = f"git clone failed: {e.stderr}" if hasattr(e, 'stderr') else str(e)
    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["message"] = str(e)
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


@app.post("/index", response_model=IndexResponse, status_code=202)
def index_repo_endpoint(body: IndexRequest, background_tasks: BackgroundTasks):
    repo_url = str(body.repo_url)

    if not _is_valid_github_url(repo_url):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL. Only public github.com repository URLs are supported.")

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "queued", "message": "Queued for indexing", "indexed_chunks": None}
    background_tasks.add_task(_start_index_job, job_id, repo_url)

    return IndexResponse(job_id=job_id, status="queued")


@app.get("/index/status/{job_id}", response_model=JobStatus)
def index_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JobStatus(job_id=job_id, status="not_found", message="No such job")
    return JobStatus(job_id=job_id, status=job.get("status", "unknown"), message=job.get("message"), indexed_chunks=job.get("indexed_chunks"))
