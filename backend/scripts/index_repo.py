# scripts/index_repo.py

import sys

from app.db.qdrant import init_collection
from app.services.parsing import extract_code_chunks
from app.services.indexing import index_chunks

from collections import Counter



def main(repo_path: str, repo_id: str):
    init_collection()  # safe to call multiple times; recreates collection
    chunks = extract_code_chunks(repo_path)
    print(f"Extracted {len(chunks)} chunks total")
    print("Chunk type distribution:", Counter(c["symbol_type"] for c in chunks))

    index_chunks(chunks, repo_id)
    print("Indexing complete")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.index_repo <repo_path> <repo_id>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
