# app/services/embedding.py

from typing import List
import numpy as np

VECTOR_SIZE = 768  # same as in qdrant.py

def embed_code_dummy(texts: List[str]) -> List[List[float]]:
    """
    Temporary dummy embedding function.
    Later we'll replace this with a real CodeBERT-based embedding.
    """
    return np.random.rand(len(texts), VECTOR_SIZE).astype("float32").tolist()
