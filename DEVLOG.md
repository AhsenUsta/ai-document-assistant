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
- Added persistent storage for the FAISS index, document chunks
  (Pickle), and metadata (JSON) to avoid rebuilding embeddings on
  every application start.
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
specific use case — This assumption was later validated against 
real test cases described in subsequent development logs.

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

Unlike the earlier COCO failure, these issues were not retrieval
failures but hallucinations caused by incomplete extraction. Since
accuracy and hallucination handling are explicit requirements of the
case study, these failures were documented rather than hidden.

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

## Day 4

### Hybrid Search Implementation

Implemented hybrid search (BM25 + semantic via Reciprocal Rank Fusion)
to address retrieval inconsistencies observed in Day 3 testing,
particularly for short, code-heavy documents (e.g., the sample
invoice) where pure semantic search sometimes failed to rank the
correct chunk highly enough.

**Regression encountered:** The first implementation used raw BM25
rank without a minimum score threshold, which allowed near-zero
lexical matches to enter the fused ranking. This caused two
previously-passing test cases to break (TÜİK financial figures — see
TESTING.md Test 11 for full details). Fixed by adding a
`bm25_min_score` threshold to exclude irrelevant lexical matches.

### Prompt Refinement: Label-Value Matching

Added explicit prompt rules to handle a recurring failure pattern:
OCR/table-flattening produces "value label value label" ordering
(e.g., a total appearing right after an unrelated preceding number),
causing the model to match the wrong number to a label. Added
instructions to match the number immediately following a label, and to
double-check similar/paired labels (e.g., active/passive totals).

This fix, combined with the hybrid search regression fix, resolved
four previously-failing test queries (see TESTING.md Test 12).

### Automated Evaluation Harness

Built `evaluate.py` + `evaluation.json` to replace manual, ad-hoc
before/after testing with a repeatable evaluation suite. Measures:
- Source Hit@K (retrieval accuracy)
- Answer Accuracy (exact-contains and keyword-contains matching)

Discovered and fixed a false negative in the evaluation script itself:
Turkish OCR output sometimes substitutes "ı" for "i" (and similar
character pairs), causing an otherwise-correct answer to fail a strict
keyword match. Added Turkish character normalization to the comparison
logic to fix this without weakening the test.

The initial benchmark achieved perfect retrieval accuracy and
highlighted one remaining generation failure. This evaluation
framework was later expanded substantially in Day 5.

### Next Steps

**Priority 1 — complete the remaining case study deliverables:**

- Build a minimal Streamlit interface for usability.
- Record a short demonstration video.

**Priority 2 — improve extraction for numeric and table-heavy documents:**

- Implement table-structure-aware extraction to preserve row/column
  relationships instead of flattening tables into plain text. For
  digital PDFs, evaluate tools such as `pdfplumber` or `camelot`; for
  scanned tables, investigate layout-aware OCR approaches using
  Tesseract TSV/hOCR output.
- Evaluate PaddleOCR as an alternative to Tesseract for the two OCR
  failure cases identified during testing: the invoice's dense
  multi-column summary section (Test 9) and Turkish character accuracy
  (Test 5). This comparison would determine whether adopting PaddleOCR
  provides measurable improvements before changing the existing OCR
  pipeline.

**Priority 3 — extend evaluation and retrieval quality:**

- Expand `evaluation.json` with the additional manually tested cases
  documented in `TESTING.md`, increasing the benchmark from 6 cases to
  approximately 15–18 cases.
- Evaluate a cross-encoder reranker to improve chunk ranking for
  challenging queries, particularly those involving numeric values and
  table-heavy documents.
  

## Day 5

### Streamlit Web Interface

Implemented a Streamlit-based chat interface (`app.py`) to satisfy the
case study's usability requirement.

Main features added:

- Automatic document indexing immediately after upload, removing the
  previous manual "Save files and build index" step.
- Dynamic document removal: deleted files are removed from `data/` and
  the retrieval index is rebuilt (or cleared if no documents remain).
- Chat-style interface using `st.chat_message` and `st.chat_input`,
  including persistent conversation history and a "Clear conversation"
  button.
- Retrieval debug mode showing retrieved chunks, sources, and
  semantic/BM25/RRF scores for troubleshooting.

### Robust Retrieval Initialization

Initially, `rag.py` attempted to load the FAISS index and BM25 cache
during module import, causing the application to fail when started with
an empty `cache/` directory.

This was resolved by making `initialize_components()` gracefully handle
a missing cache and allowing `generate_answer()` to return an
informative "no documents indexed yet" message instead of raising an
exception.

### Streamlit Cache Issue

While implementing incremental indexing, I discovered that
`st.cache_resource` was unsuitable for this use case.

Although newly uploaded documents were indexed correctly on disk,
Streamlit continued serving stale retrieval objects from memory.
Replacing the cache mechanism with an explicit
`st.session_state["rag_initialized"]` flag together with a manual
`reload_retrieval_components()` call made the indexing behaviour fully
predictable.

### Retrieval Limitation: Large Documents

Testing revealed that one significantly larger document could dominate
the retrieval results even for unrelated questions.

The issue appears to result from the much larger number of candidate
chunks contributed by a single document when using a fixed `TOP_K`
retrieval strategy.

The limitation was documented for future work rather than addressed in
this iteration.

### Language-Aware Fallback Responses

The prompt instructed the LLM to return the "not found" message in the
same language as the user's question. In practice this proved
inconsistent.

To guarantee deterministic behaviour, question language detection was
added in `rag.py`, and the fallback response is normalized after
generation when necessary. This ensures consistent multilingual
responses without relying entirely on prompt following.

### Model Upgrade

Replaced the default model (`qwen3:1.7b`) with `qwen3:8b`.

The larger model resolved several retrieval-disambiguation failures,
particularly for invoice and TÜBİTAK questions.

However, testing also revealed a trade-off: when OCR failed to extract
the invoice total, `qwen3:1.7b` correctly declined to answer, whereas
`qwen3:8b` confidently returned an incorrect subtotal. This behaviour
is documented in `TESTING.md`.

### Retrieval Configuration

Separated retrieval breadth from LLM context size.

- `TOP_K = 15` retrieval candidates
- `MAX_CONTEXTS = 5` chunks provided to the LLM

This improved recall while keeping the prompt size unchanged.

During testing, the previously introduced `MIN_SCORE` threshold was
found to have no measurable benefit for the current corpus and was
removed.

### Automated Evaluation

Expanded the benchmark from 6 to 32 evaluation cases covering:

- Invoice documents
- TÜİK financial tables
- COCO documentation
- TÜBİTAK documentation
- EPA SOP documents
- Deliberate "not found" questions for hallucination testing

Evaluation also revealed that several reported failures were caused by
the benchmark itself rather than incorrect model behaviour. After the
application began returning language-specific fallback responses, the
evaluation script still expected only the original English fallback.
The evaluation logic was updated accordingly to correctly evaluate
multilingual "not found" responses.

### Next Steps

- Record the demonstration video.
- Add per-source result capping to prevent large documents dominating
  retrieval.
- Implement table-aware extraction (`pdfplumber` / `camelot` for
  digital PDFs and layout-aware OCR for scanned tables).
- Evaluate PaddleOCR as an alternative OCR engine.
- Investigate cross-encoder reranking to improve retrieval quality.

## Summary

Over five development iterations the project evolved from a basic OCR
pipeline into a multilingual RAG assistant supporting:

- OCR for PDFs and images
- Hybrid retrieval (semantic + BM25)
- Local LLM answering via Ollama
- Streamlit chat interface
- Incremental document indexing
- Automated evaluation framework
- Multilingual fallback handling

Several known limitations remain, particularly around table extraction
and retrieval balancing for highly imbalanced document collections.
These are documented throughout the development log and in TESTING.md.