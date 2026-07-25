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

## Day 3

### RAG Integration

#### Implemented
- Integrated the FAISS retriever with a local LLM via Ollama (`rag.py`).
- Built a prompt template that grounds answers strictly in retrieved
  context and instructs the model to respond with a fixed fallback
  message when the answer isn't present in the documents.
- Tested the full pipeline end-to-end with real documents (digital
  TR/EN PDFs, OCR TR/EN PDFs, OCR TR JPG/PNG).

### Technical Decision: Switching from qwen3:4b to qwen3:1.7b

**Problem:** Response times were very slow. Investigated using
`ollama ps` and found the model was split across CPU/GPU
(27-45% CPU / 55-73% GPU) instead of running fully on GPU.

**Diagnosis:**
- Checked `nvidia-smi`: RTX 3050 has only 4GB VRAM, with ~774MB
  already used by the driver/OS, leaving ~3.3GB free.
- `qwen3:4b` (2.5GB on disk) plus the KV cache for `num_ctx: 8192`
  exceeded the available VRAM, forcing Ollama to offload layers to CPU.
- Reduced `num_ctx` to 2048; the model still partially offloaded to CPU
  (27%/73%), meaning context size alone wasn't the full explanation —
  the 4b model itself was too large for this card's headroom once
  runtime overhead is included.

**Decision:** Switched to `qwen3:1.7b` (1.4GB), which loads at 100% GPU
with no CPU offloading. Since the RAG task is primarily extraction /
summarization from provided context rather than open-ended reasoning,
a smaller model was expected to have limited quality impact for this
specific use case — this needs to be, and was later partially,
validated against real failures (see below).

**Result:** 100% GPU utilization, noticeably faster response times.

### Debugging: Retrieval vs Generation Failure

**Problem:** Asking "COCO kaç görüntü içeriyor?" (a question whose
answer exists verbatim in an OCR'd document) consistently returned
"I could not find the answer in the provided documents" — a likely
false negative, since the answer (330K images) is present in the
source text.

**Debugging process:**
1. Bypassed the LLM and inspected raw retrieval using `search.py`
   directly. Found the correct chunk was retrieved with a similarity
   score of 0.57-0.58, ranked 3rd-4th out of 5 — meaning retrieval was
   working correctly.
2. Isolated variables by removing OCR'd files (`.jpg`/`.png`) from
   `data/` and re-testing with only the clean digital PDF present.
   Discovered the digital PDF used in this experiment didn't actually
   contain the COCO content (my test file naming was misleading — the
   `digital_*` files turned out to be different topics than expected).
   This ruled out one hypothesis but didn't explain the original
   failure, since the failure was reproduced separately with the OCR
   files present and retrieval confirmed correct.
3. Re-ran the original failing query 3+ times with OCR files present:
   the model consistently failed to extract the answer even though it
   was present in the retrieved context.

**Conclusion:** This is a generation-level failure, not a retrieval
failure. Likely cause: OCR-degraded text (e.g. "tizere", "gériinti"
instead of clean Turkish) reduces the small model's (`qwen3:1.7b`)
confidence in extracting a specific numeric fact from noisy context,
causing it to default to the "not found" fallback defined in the
prompt.

**Decision:** Did not attempt to fix this in this iteration. A proper
fix would require either OCR post-processing/cleanup, deduplication of
near-identical chunks (the `.jpg`/`.png` duplicates reduce effective
context diversity within `TOP_K`), or testing with a larger model —
each a nontrivial addition beyond the current scope. Documented as a
known limitation in `TESTING.md` instead, along with the full
diagnostic trail.

### Testing: Table and Invoice Numeric Extraction

Extended testing to include a Turkish financial statement (TÜİK
balance sheet, digital PDF) and a scanned invoice (OCR'd PDF), to
cover the "tablolu belge" (tabular document) scenario required by the
case study.

**Findings (full detail in `TESTING.md` Tests 7-10):**
- The invoice's grand total was never extracted by OCR at all — a
  pure extraction-level gap, confirmed by inspecting cached chunks
  directly.
- Several numeric queries against the financial table returned
  hallucinated figures, in one case with an entirely fabricated
  calculation/formula presented as if it were derived from the
  source data.
- Simple categorical queries (tax rate, absence of a due date) were
  still handled correctly.

This is a more serious class of failure than the earlier
retrieval/generation gap (COCO test): the model doesn't just miss
information, it sometimes fabricates confident-sounding numbers and
reasoning. This is exactly the "doğruluk" (accuracy/no hallucination)
requirement the case study asks about, so it was tested thoroughly and
documented rather than glossed over.

### Note: Table-Structure-Aware Extraction Not Yet Implemented

The failures above point to a common underlying gap: the current
pipeline flattens tables into plain text during extraction, which
loses row/column structure and can separate summary/total figures
from their supporting rows.

Table-aware extraction (e.g., `pdfplumber` or `camelot` for digital
PDFs, bounding-box-based OCR reconstruction for scanned tables) would
likely address this, but has not been implemented in the current
version. This is a meaningfully different extraction path from the
current flat-text pipeline — digital and scanned tables would need
separate strategies.

For now, this is documented as a known limitation (see Tests 7-10 in
`TESTING.md`) rather than addressed, so that the failure mode is
understood and traceable. If the project continues past its current
scope, this would be a natural next step: `pdfplumber`/`camelot` for
digital PDFs and Tesseract's TSV/hOCR output (which preserves bounding
boxes) for scanned tables, to keep row/column relationships intact
through chunking.

### Next Steps
- Add duplicate chunk detection (still open from Day 2)
- Consider OCR text cleanup/post-processing for noisy characters
- Test whether a larger model (qwen3:4b/8b) resolves the generation
  failure above, if a machine with more VRAM becomes available
- Build a minimal interface (Streamlit or FastAPI) for usability
- Record demo video