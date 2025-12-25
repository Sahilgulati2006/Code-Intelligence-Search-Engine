# app/services/indexing.py

from typing import List, Dict, Any
import uuid
from collections import Counter

from qdrant_client.models import PointStruct

from app.db.qdrant import client
from app.services.embedding import embed_code_chunks

VECTOR_SIZE = 768  # must match CodeBERT + qdrant config
BATCH_SIZE = 64    # safe batch size for CPU embedding


def index_chunks(chunks: List[Dict[str, Any]], repo_id: str):
    if not chunks:
        print(f"No chunks to index for repo_id={repo_id}. Skipping Qdrant upsert.")
        return

    # 🔍 Debug: see what we are indexing
    type_counts = Counter(c.get("symbol_type") for c in chunks)
    print(f"Chunk type distribution: {dict(type_counts)}")

    total_indexed = 0

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["code"] for c in batch]

        vectors = embed_code_chunks(texts)

        points = []
        for chunk, vec in zip(batch, vectors):
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

        total_indexed += len(points)
        print(f"Indexed {total_indexed}/{len(chunks)} chunks...")

    print(f"Indexing complete: {total_indexed} chunks indexed into Qdrant.")
