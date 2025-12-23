# app/services/indexing.py

from typing import List, Dict, Any
import uuid

from qdrant_client.models import PointStruct

from app.db.qdrant import client
from app.services.embedding import embed_code_chunks

VECTOR_SIZE = 768  # must match CodeBERT + qdrant config


def index_chunks(chunks: List[Dict[str, Any]], repo_id: str):
    if not chunks:
        print(f"No chunks to index for repo_id={repo_id}. Skipping Qdrant upsert.")
        return

    texts = [c["code"] for c in chunks]
    vectors = embed_code_chunks(texts)  # REAL embeddings

    points = []
    for chunk, vec in zip(chunks, vectors):
        points.append(
            PointStruct(
                id=int(uuid.uuid4().int % (2**63 - 1)),
                vector=vec,
                payload={
                    **chunk,
                    "repo_id": repo_id,
                },
            )
        )

    client.upsert(
        collection_name="code_chunks",
        points=points,
    )
    print(f"Indexed {len(points)} chunks into Qdrant.")
