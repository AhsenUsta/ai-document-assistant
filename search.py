import pickle
import time

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config import (
    CHUNKS_PATH,
    EMBEDDING_MODEL,
    INDEX_PATH,
    TOP_K,
)


def normalize(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors for cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def load_cache() -> tuple[faiss.Index, list[dict]]:
    """Load FAISS index and document chunks from disk."""
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"FAISS index could not be found: {INDEX_PATH}")

    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Chunks cache could not be found: {CHUNKS_PATH}")

    index = faiss.read_index(str(INDEX_PATH))

    with CHUNKS_PATH.open("rb") as file:
        chunks = pickle.load(file)

    if index.ntotal != len(chunks):
        raise ValueError(f"FAISS vector count and chunk count do not match. Vectors: {index.ntotal}, chunks: {len(chunks)}")

    return index, chunks


def semantic_search(query: str,model: SentenceTransformer,index: faiss.Index,chunks: list[dict],top_k: int = TOP_K,) -> list[dict]:
    """Return the most relevant chunks for a query."""
    query_embedding = model.encode([query],convert_to_numpy=True,).astype("float32")

    query_embedding = normalize(query_embedding)

    scores, indices = index.search(query_embedding, top_k)

    results = []

    for score, chunk_index in zip(scores[0], indices[0]):
        if chunk_index < 0:
            continue

        chunk = chunks[chunk_index]

        results.append(
            {
                "score": float(score),
                "source": chunk["source"],
                "text": chunk["text"],
            }
        )

    return results


def main() -> None:
    total_start = time.perf_counter()

    print("Loading semantic search components...")

    model_start = time.perf_counter()
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"[TIMING] model load: {time.perf_counter() - model_start:.3f}s")

    cache_start = time.perf_counter()
    index, chunks = load_cache()

    print(f"[TIMING] cache load: {time.perf_counter() - cache_start:.3f}s")

    print(f"Loaded vectors: {index.ntotal}")
    print(f"Loaded chunks: {len(chunks)}")

    while True:
        query = input("\nQuestion (type 'exit' to quit): ").strip()

        if query.lower() in {"exit", "quit"}:
            print("Semantic search stopped.")
            break

        if not query:
            print("Please enter a question.")
            continue

        search_start = time.perf_counter()

        results = semantic_search(query=query,model=model,index=index,chunks=chunks,top_k=TOP_K,)

        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        for position, result in enumerate(results, start=1):
            print(
                f"\n{position}. "
                f"Score: {result['score']:.4f} | "
                f"Source: {result['source']}"
            )
            print("-" * 70)
            print(result["text"])

        print(f"[TIMING] semantic search: {time.perf_counter() - search_start:.3f}s")


if __name__ == "__main__":
    main()