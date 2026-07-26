import json
import pickle
import time

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from search import create_bm25

from config import (
    CACHE_ROOT,
    CHUNKS_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_ROOT,
    EMBEDDING_MODEL,
    INDEX_PATH,
    META_PATH,
    BM25_PATH,
)
from loaddocs import load_documents_from_folder


def normalize(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors for cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def create_embeddings(chunks: list[dict],model: SentenceTransformer,) -> np.ndarray:
    """Create normalized embeddings from document chunks."""
    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True,
    ).astype("float32")

    return normalize(embeddings)


def create_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """Create a FAISS index using cosine similarity."""
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


def save_cache(index: faiss.Index,chunks: list[dict],embedding_dimension: int,) -> None:
    """Save FAISS index, chunks and metadata to disk."""
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_PATH))

    with CHUNKS_PATH.open("wb") as file:
        pickle.dump(chunks, file)

    metadata = {
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": embedding_dimension,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "num_chunks": len(chunks),
    }

    with META_PATH.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=4)
    
    # Persist the BM25 index so it doesn't need to be rebuilt on every load
    bm25 = create_bm25(chunks)
    with (BM25_PATH).open("wb") as file:
        pickle.dump(bm25, file)

def rebuild_index() -> dict:
    total_start = time.perf_counter()

    chunks = load_documents_from_folder(DATA_ROOT)

    if not chunks:
        raise ValueError("No chunks were generated.")

    model_start = time.perf_counter()
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(
        f"[TIMING] model load: "
        f"{time.perf_counter() - model_start:.3f}s"
    )

    embedding_start = time.perf_counter()
    embeddings = create_embeddings(chunks, model)

    print(
        f"[TIMING] embedding generation: "
        f"{time.perf_counter() - embedding_start:.3f}s"
    )

    index = create_faiss_index(embeddings)

    save_start = time.perf_counter()

    save_cache(
        index=index,
        chunks=chunks,
        embedding_dimension=embeddings.shape[1],
    )

    print(
        f"[TIMING] cache save: "
        f"{time.perf_counter() - save_start:.3f}s"
    )

    indexed_files = sorted({
        chunk["source"]
        for chunk in chunks
    })

    total_duration = time.perf_counter() - total_start

    print("=" * 60)
    print(f"Chunks: {len(chunks)}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"FAISS vectors: {index.ntotal}")
    print(f"Index saved: {INDEX_PATH}")
    print(f"Chunks saved: {CHUNKS_PATH}")
    print(f"Metadata saved: {META_PATH}")
    print(f"[TIMING] indexer TOTAL: {total_duration:.3f}s")
    print("=" * 60)

    return {
        "indexed_files": indexed_files,
        "chunk_count": len(chunks),
        "embedding_dimension": int(embeddings.shape[1]),
        "faiss_vectors": int(index.ntotal),
        "duration": round(total_duration, 3),
    }


def main() -> None:
    rebuild_index()


if __name__ == "__main__":
    main()