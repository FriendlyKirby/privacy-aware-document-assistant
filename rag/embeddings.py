"""Embedding helpers for the local RAG pipeline."""

import numpy as np
from sentence_transformers import SentenceTransformer


def load_embedding_model(model_name="all-MiniLM-L6-v2"):
    """Load a sentence-transformers embedding model.

    Args:
        model_name: Name of the sentence-transformers model to load.

    Returns:
        A loaded SentenceTransformer model.
    """
    return SentenceTransformer(model_name)


def embed_texts(model, texts):
    """Create normalized embeddings for a list of texts.

    Normalized vectors work well with FAISS inner-product search because the
    inner product becomes cosine similarity.

    Args:
        model: A loaded SentenceTransformer model.
        texts: List of strings to embed.

    Returns:
        A float32 NumPy array of shape `(number_of_texts, embedding_size)`.
    """
    if not texts:
        return np.empty((0, 0), dtype="float32")

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return np.asarray(embeddings, dtype="float32")


def embed_query(model, query):
    """Create a normalized embedding for one user question.

    Args:
        model: A loaded SentenceTransformer model.
        query: User question as a string.

    Returns:
        A float32 NumPy array with one query embedding.
    """
    return embed_texts(model, [query])
