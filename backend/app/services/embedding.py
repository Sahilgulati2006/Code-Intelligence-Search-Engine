# app/services/embedding.py

from typing import List
import torch
from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "microsoft/codebert-base"
DEVICE = "cpu"  # set to "cuda" later if you have GPU

_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
_model = AutoModel.from_pretrained(MODEL_NAME)
_model.to(DEVICE)
_model.eval()


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Shared helper: turn a list of code/text strings into embeddings
    using CodeBERT (mean pooled last hidden state).
    """
    with torch.no_grad():
        encoded = _tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )
        encoded = {k: v.to(DEVICE) for k, v in encoded.items()}
        outputs = _model(**encoded)
        # outputs.last_hidden_state: [batch, seq_len, hidden_size]
        last_hidden = outputs.last_hidden_state  # (B, T, 768)
        embeddings = last_hidden.mean(dim=1)     # (B, 768)
        embeddings = embeddings.cpu().numpy()
    return embeddings.tolist()


def embed_code_chunks(texts: List[str]) -> List[List[float]]:
    """
    Embeddings for code snippets (functions/classes).
    """
    return _embed_texts(texts)


def embed_query_text(text: str) -> List[float]:
    """
    Embedding for a single natural language or code query.
    """
    return _embed_texts([text])[0]
