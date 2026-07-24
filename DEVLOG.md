# Dev Log

## Day 1

- Created project structure.
- Implemented PDF text extraction using PyMuPDF.
- Added OCR support using Tesseract.
- Added image OCR support.
- Implemented text chunking.
- Improved chunking to avoid splitting words.
- Tested with digital PDFs, scanned PDFs, PNG and JPG images.

## Day 2

### Semantic Search and FAISS Integration

### Implemented

- Added multilingual sentence embeddings using
  `paraphrase-multilingual-mpnet-base-v2`.
- Converted document chunks into 768-dimensional vectors.
- Added FAISS vector indexing.
- Normalized document and query embeddings for cosine similarity search.
- Added persistent FAISS index storage.
- Added persistent chunk storage using Pickle.
- Added index metadata storage using JSON.
- Added semantic search through `search.py`.
- Added validation between FAISS vector count and cached chunk count.
- Added configurable `TOP_K` value.
- Added execution time measurements for:
  - model loading
  - cache loading
  - semantic search
  
### Technical Decisions

#### Multilingual Embedding Model

The project uses the following multilingual embedding model:

```text
sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

#### Persistent Cache

The generated FAISS index and document chunks are stored on disk to avoid
rebuilding embeddings on every application start.

#### Cosine Similarity

Document and query embeddings are normalized before searching the FAISS
index so that inner-product search behaves as cosine similarity.

### Observations

The same OCR document existed as both `.png` and `.jpg`. Because both
files contained the same content, duplicate semantic search results were
returned.

This is not a FAISS error. Duplicate-content detection or result
deduplication may be added in a later stage.

### Next Steps

- Add metadata validation
- Add duplicate chunk detection
- Add minimum similarity-score filtering
- Add BM25 keyword search
- Add hybrid retrieval
- Integrate the retriever with an LLM
- Expose the pipeline through FastAPI