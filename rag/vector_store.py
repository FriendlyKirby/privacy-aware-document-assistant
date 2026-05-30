"""FAISS vector index helpers for local similarity search."""

import numpy as np


def build_faiss_index(embeddings):
    """Build a FAISS index from normalized embeddings.

    This project uses normalized vectors with `IndexFlatIP`, so higher scores
    mean more similar text.

    Args:
        embeddings: NumPy array of document chunk embeddings.

    Returns:
        A FAISS index, or None if there are no embeddings.
    """
    if embeddings is None or embeddings.size == 0:
        return None

    import faiss

    clean_embeddings = np.asarray(embeddings, dtype="float32")
    dimension = clean_embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(clean_embeddings)
    return index


def search_index(index, query_embedding, chunks, top_k=3, min_score=0.35):
    """Search a FAISS index for the most relevant chunks.

    Args:
        index: A FAISS index created by build_faiss_index.
        query_embedding: Embedding for the user question.
        chunks: List of chunk dictionaries aligned with the index.
        top_k: Number of chunks to return.
        min_score: Minimum similarity score required for a chunk to be included.

    Returns:
        A list of retrieved chunk dictionaries. Each result includes text,
        source, title, chunk_index, and score.
    """
    if index is None or query_embedding is None or not chunks:
        return []

    if query_embedding.size == 0:
        return []

    safe_top_k = min(top_k, len(chunks))
    distances, indices = index.search(
        np.asarray(query_embedding, dtype="float32"),
        safe_top_k,
    )

    results = []

    for score, chunk_index in zip(distances[0], indices[0]):
        if chunk_index < 0 or chunk_index >= len(chunks):
            continue

        result = chunks[chunk_index].copy()
        result["score"] = float(score)
        results.append(result)

    filtered_results = [
        result for result in results if result.get("score", 0.0) >= min_score
    ]

    # Keep the single best result if all scores are below the threshold. This
    # avoids an empty answer when the best available match is still useful.
    if not filtered_results and results:
        return [results[0]]

    return filtered_results
