# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.search import SearchRequest, SearchResponse
from app.services.search import search_code

app = FastAPI(title="Code Intelligence Backend")

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
