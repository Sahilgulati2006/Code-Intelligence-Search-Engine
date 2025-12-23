# app/main.py

from fastapi import FastAPI

from app.models.search import SearchRequest, SearchResponse
from app.services.search import search_code

app = FastAPI(title="Code Intelligence Backend")


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
