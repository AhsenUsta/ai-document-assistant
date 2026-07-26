import pickle
import time
import re
import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from config import (
    CHUNKS_PATH,
    EMBEDDING_MODEL,
    INDEX_PATH,
    TOP_K,
    CACHE_ROOT,
    BM25_PATH,
)

def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower(), flags=re.UNICODE,)
    
def normalize(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors for cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms
    
def create_bm25(chunks: list[dict]) -> BM25Okapi:
    tokenized_chunks = [
        tokenize(chunk["text"])
        for chunk in chunks
    ]

    return BM25Okapi(tokenized_chunks)

def load_cache() -> tuple[faiss.Index, list[dict], BM25Okapi]:
    """Load FAISS index, document chunks, and BM25 index from disk."""
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"FAISS index could not be found: {INDEX_PATH}")

    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Chunks cache could not be found: {CHUNKS_PATH}")

    index = faiss.read_index(str(INDEX_PATH))

    with CHUNKS_PATH.open("rb") as file:
        chunks = pickle.load(file)

    if index.ntotal != len(chunks):
        raise ValueError(f"FAISS vector count and chunk count do not match. Vectors: {index.ntotal}, chunks: {len(chunks)}")

    if BM25_PATH.exists():
        with BM25_PATH.open("rb") as file:
            bm25 = pickle.load(file)
    else:
        # Fallback for older cache versions without a saved BM25 index
        bm25 = create_bm25(chunks)

    return index, chunks, bm25

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

def hybrid_search(query: str, model: SentenceTransformer, index: faiss.Index, chunks: list[dict], bm25: BM25Okapi, top_k: int = 5, candidate_count: int = 30, rrf_k: int = 60, bm25_min_score: float = 1e-6,) -> list[dict]:

    if not chunks:
        return []

    candidate_count = min(candidate_count, len(chunks))

    # 1. Semantic retrieval
    query_embedding = model.encode([query], convert_to_numpy=True, ).astype("float32")

    faiss.normalize_L2(query_embedding)

    semantic_scores, semantic_indices = index.search(query_embedding,candidate_count,)

    semantic_ranking = [
        int(index_value)
        for index_value in semantic_indices[0]
        if index_value >= 0
    ]

    semantic_score_map = {
        int(index_value): float(score)
        for index_value, score in zip(
            semantic_indices[0],
            semantic_scores[0],
        )
        if index_value >= 0
    }

    # 2. Lexical retrieval
    query_tokens = tokenize(query)
    
    lexical_scores = bm25.get_scores(query_tokens)
    
    lexical_ranking = [
        int(i) for i in np.argsort(lexical_scores)[::-1][:candidate_count]
        if lexical_scores[i] > bm25_min_score
    ]

    # 3. Reciprocal Rank Fusion
    fused_scores: dict[int, float] = {}

    for rank, chunk_index in enumerate(semantic_ranking, start=1,):
        fused_scores[chunk_index] = (
            fused_scores.get(chunk_index, 0.0)
            + 1.0 / (rrf_k + rank)
        )

    for rank, chunk_index in enumerate(lexical_ranking, start=1,):
        fused_scores[chunk_index] = (
            fused_scores.get(chunk_index, 0.0)
            + 1.0 / (rrf_k + rank)
        )

    ranked_indices = sorted(fused_scores, key=fused_scores.get, reverse=True,)[:top_k]

    results = []

    for chunk_index in ranked_indices:
        chunk = chunks[chunk_index]

        results.append({
            "score": fused_scores[chunk_index],
            "semantic_score": semantic_score_map.get(chunk_index, 0.0),
            "bm25_score": float(lexical_scores[chunk_index]),
            "source": chunk["source"],
            "text": chunk["text"],
            "chunk_index": chunk_index,
        })

    return results

def main() -> None:
    total_start = time.perf_counter()

    print("Loading semantic search components...")

    model_start = time.perf_counter()
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"[TIMING] model load: {time.perf_counter() - model_start:.3f}s")

    cache_start = time.perf_counter()
    index, chunks, bm25 = load_cache()

    print(f"[TIMING] cache load: {time.perf_counter() - cache_start:.3f}s")
    
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

        results = hybrid_search(query=query, model=model, index=index, chunks=chunks, bm25=bm25, top_k=TOP_K,)

        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        for position, result in enumerate(results, start=1):
            print(f"\n[{position}]")
            print(f"Hybrid score : {result['score']:.6f}")
            print(f"Semantic     : {result['semantic_score']:.4f}")
            print(f"BM25         : {result['bm25_score']:.4f}")
            print(f"Source       : {result['source']}")
            print("-" * 70)
            print(result["text"])

        print(f"[TIMING] hybrid search: {time.perf_counter() - search_start:.3f}s")
        


if __name__ == "__main__":
    main()