# Dev Log

## Day 1

### Initial Project Setup

- Created the initial project structure.
- Implemented PDF text extraction using **PyMuPDF**.
- Added OCR support using **Tesseract OCR** for scanned documents.
- Added OCR support for standalone image files (PNG and JPG).
- Implemented text chunking for retrieval.
- Improved the chunking algorithm to avoid splitting words across chunk boundaries.
- Validated the extraction pipeline using digital PDFs, scanned PDFs, PNG images, and JPG images.

**Outcome**

By the end of Day 1, the project was able to extract text from both
digital and scanned documents, providing the foundation for the later
retrieval and question-answering pipeline.

## Day 2

### Semantic Search and FAISS Integration

### Implemented

- Added multilingual sentence embeddings using
  `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`.
- Converted document chunks into 768-dimensional embedding vectors.
- Integrated FAISS for semantic vector indexing.
- Normalized both document and query embeddings to enable cosine similarity search.
- Added persistent storage for the FAISS index, document chunks (Pickle), and metadata (JSON) to avoid rebuilding embeddings on every application start.
- Implemented semantic search in `search.py`.
- Added validation to ensure the number of FAISS vectors matches the number of cached document chunks.
- Added a configurable `TOP_K` retrieval parameter.
- Added execution time measurements for:
  - Model loading
  - Cache loading
  - Semantic search

### Technical Decisions

#### Multilingual Embedding Model

The project uses the following multilingual embedding model:

```text
sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

This model was selected to support semantic retrieval across both
Turkish and English documents without maintaining separate embedding
models.

#### Persistent Cache

The generated FAISS index and document chunks are stored on disk to
avoid rebuilding embeddings on every application start, significantly
reducing application startup time.

#### Cosine Similarity

Document and query embeddings are normalized before searching the FAISS
index so that inner-product search behaves as cosine similarity.

### Observations

The same OCR document existed as both `.png` and `.jpg`. Because both
files contained identical content, semantic search returned duplicate
results.

This behavior is expected because FAISS indexes vector similarity
without considering document uniqueness. Duplicate-content detection
or result deduplication was identified as a future improvement.

## Day 3

### RAG Integration

### Implemented

- Integrated the FAISS retriever with a local LLM using Ollama (`rag.py`).
- Implemented a prompt template that restricts answers to the retrieved
  context and returns a fixed fallback message when no answer is found.
- Validated the complete RAG pipeline using both digital and OCR
  documents in Turkish and English.

### Technical Decisions

### Switching to a Smaller Model

Initial testing with `qwen3:4b` resulted in slow response times because
the model exceeded the available VRAM on the development machine
(RTX 3050, 4 GB), causing partial CPU offloading.

The project was therefore switched to `qwen3:1.7b`, which runs entirely
on the GPU and provides significantly faster inference while maintaining
sufficient quality for retrieval-augmented question answering.

### Investigation: Retrieval vs. Generation

While testing OCR documents, some questions returned the fallback
message even though the correct information had been retrieved.

To isolate the issue, retrieval was inspected independently using
`search.py`. The correct document chunks were consistently retrieved,
indicating that retrieval was functioning correctly.

The investigation showed that these failures originated during answer
generation rather than retrieval, particularly when OCR introduced noisy
text around numeric values.

The issue was documented as a known limitation instead of being addressed
within the current project scope.

### Extended Evaluation

Additional testing was performed using financial tables and scanned
invoices.

The evaluation identified two important limitations:

- OCR may fail to extract important values from dense tabular layouts.
- Numeric question answering becomes less reliable when OCR output is
  incomplete or degraded.

These findings were documented in `TESTING.md` and influenced the final
scope of the project.

### Observation

By the end of Day 3, the project had evolved into a complete local RAG
pipeline consisting of OCR, semantic retrieval, and LLM-based question
answering. Most remaining issues were related to document extraction
quality rather than the retrieval architecture itself.

## Day 4

### Hybrid Retrieval and Evaluation

### Implemented

- Implemented hybrid retrieval by combining semantic search (FAISS)
  and BM25 using Reciprocal Rank Fusion (RRF).
- Added a minimum BM25 score threshold to prevent irrelevant lexical
  matches from degrading retrieval quality.
- Refined the prompt with explicit label-to-value matching rules to
  improve numeric extraction from OCR-generated tables.
- Developed an automated evaluation framework consisting of
  `evaluate.py` and `evaluation.json`.

### Technical Decisions

#### Hybrid Retrieval

Pure semantic retrieval performed well for narrative documents but
occasionally ranked incorrect chunks for short, keyword-heavy content
such as invoices.

To improve retrieval consistency, BM25 was combined with semantic
search using Reciprocal Rank Fusion. A minimum BM25 score threshold
was introduced after regression testing showed that near-zero lexical
matches could negatively influence the final ranking.

#### Prompt Refinement

Additional prompt instructions were introduced to reduce incorrect
label-to-value associations caused by flattened OCR table layouts.

The model is explicitly instructed to associate values with the labels
that immediately precede them, reducing ambiguity when multiple numeric
fields appear close together.

### Automated Evaluation

A repeatable evaluation framework replaced manual testing by measuring:

- Retrieval accuracy (Source Hit@K)
- Answer accuracy

During implementation, the evaluation script itself was improved by
normalizing Turkish characters before keyword comparison, eliminating
false negatives caused by OCR character variations.

### Observation

Hybrid retrieval improved retrieval robustness while the automated
evaluation framework made future improvements measurable and
repeatable. The remaining issues were concentrated in OCR quality and
complex numeric reasoning rather than retrieval performance.
  

## Day 5

### FastAPI Web Interface and Final Improvements

### Implemented

- Replaced the initial Streamlit prototype with a FastAPI-based web
  application using HTML, CSS, and JavaScript.
- Added REST endpoints for document upload and question answering.
- Implemented automatic document indexing after upload.
- Added document removal with automatic index rebuilding.
- Built a browser-based chat interface with loading indicators.
- Added retrieval diagnostics for development, including retrieved
  chunks, source documents, and retrieval scores.
  - Added a **Clear Documents** feature to remove uploaded documents,
  clear cached retrieval data, and reset the in-memory retrieval
  components without restarting the server.

### Retrieval Improvements

The retrieval pipeline was updated to reload the FAISS index, BM25
index, and cached metadata automatically whenever documents are added
or removed, keeping the running application synchronized without
requiring a server restart.

Retrieval breadth was separated from LLM context size by introducing:

- `TOP_K = 15` retrieval candidates
- `MAX_CONTEXTS = 5` chunks provided to the language model

This improved retrieval recall while keeping prompt size and inference
cost stable.

### Robust Application Startup

The application was updated to handle an empty cache directory
gracefully.

Instead of failing during startup, the system now reports that no
documents have been indexed and becomes fully operational immediately
after the first document upload.

### Language-Aware Responses

Language detection was added to normalize fallback responses when the
model returned the "not found" message in an unexpected language.

This provides deterministic multilingual behaviour independent of
prompt compliance.

### Model Evaluation

The default language model was upgraded from `qwen3:1.7b` to
`qwen3:8b`.

Testing showed improved answer quality for several retrieval tasks,
while also revealing that larger models may hallucinate numerical
values more confidently when OCR extraction is incomplete. This
behaviour is documented in `TESTING.md`.

### Automated Evaluation

The evaluation benchmark was expanded from 6 to 32 test cases covering
multiple document types, including invoices, financial tables,
technical documentation, and negative ("not found") queries.

The evaluation framework was also refined to correctly handle
multilingual fallback responses after language-aware answer
normalization was introduced.

### Observation

By the end of Day 5, the project had evolved into a complete local
document question-answering system featuring OCR, hybrid retrieval,
LLM-based answer generation, automated benchmarking, and a FastAPI web
interface. The remaining limitations were primarily related to OCR
quality and complex tabular document extraction rather than the overall
system architecture.

## Summary

Over five development iterations, the project evolved from a basic OCR
pipeline into a complete local document question-answering system.

The final implementation includes:

- OCR for PDFs and images
- Hybrid retrieval (FAISS + BM25)
- Local LLM-based answer generation with Ollama
- FastAPI web application
- HTML/CSS/JavaScript frontend
- Automatic document indexing and re-indexing
- Automated evaluation framework
- Multilingual question answering
- Language-aware fallback responses

Throughout development, several engineering decisions were driven by
systematic testing, including model selection, retrieval improvements,
prompt refinement, and evaluation methodology.

The remaining limitations are primarily related to OCR quality, dense
tabular document layouts, and numeric question answering rather than
the retrieval architecture itself. These limitations are documented in
`TESTING.md` together with the corresponding design decisions.

## What I Would Do Differently If I Started Again

If I were starting this project again with the knowledge gained during
development and testing, I would make several architectural decisions earlier.

### 1. Build the evaluation framework before optimizing the pipeline

The automated evaluation suite was added after several manual tests had already
been performed.

Starting with a small but representative benchmark would have made it easier to
measure the effect of each change and detect regressions earlier.

I would define evaluation cases for:

- Digital and scanned documents
- Turkish and English queries
- Numeric extraction
- Cross-language retrieval
- Hallucination and "not found" behaviour
- Table-heavy documents

This would allow retrieval, extraction, and generation changes to be evaluated
independently from the beginning.

### 2. Separate extraction, retrieval, and generation failures earlier

During development, some incorrect answers initially appeared to be retrieval
problems. Direct inspection of extracted text and retrieved chunks later showed
that failures could occur at three different stages:

1. The information was not extracted from the document.
2. The information was extracted but not retrieved.
3. The correct chunk was retrieved, but the LLM failed to use it.

If starting again, I would add diagnostic tools for all three stages from the
first iteration:

- Raw extracted text inspection
- Chunk inspection
- Retrieval score display
- Final prompt and context inspection
- Structured evaluation logs

This would reduce debugging time and make root-cause analysis more systematic.

### 3. Design table handling as a separate extraction path

The original pipeline treated all document content as flattened plain text.

This worked well for narrative documents but caused problems for financial
tables and scanned invoices because row and column relationships were lost.

If starting again, I would separate document extraction into different
strategies:

- Standard text extraction for narrative digital PDFs
- Table-aware extraction for digital tables
- Layout-aware OCR for scanned tables
- Standard OCR for regular scanned pages and images

Tools such as `pdfplumber` or `camelot` could be evaluated for digital tables,
while Tesseract TSV/hOCR or another layout-aware OCR solution could be used for
scanned tables.

### 4. Avoid global full-index rebuilding for every document change

The current implementation rebuilds the complete index when documents are
added or removed.

This is acceptable for the current case-study dataset, but it would become
inefficient as the number or size of documents increases.

If starting again, I would design document-level incremental indexing:

- Store document IDs with each chunk.
- Add vectors only for newly uploaded documents.
- Remove vectors and metadata only for deleted documents.
- Keep index and metadata updates atomic.

This would improve scalability and reduce processing time.

### 5. Add duplicate-content detection during ingestion

Testing showed that identical content stored as both JPG and PNG produced
duplicate chunks and reduced context diversity.

If starting again, I would calculate a document or chunk hash during ingestion
and skip exact duplicates before creating embeddings.

Near-duplicate chunk detection could also be added later if necessary.

### 6. Keep retrieval candidates balanced across documents

A large document can contribute many more chunks than smaller documents and
dominate the candidate set.

If starting again, I would introduce per-source retrieval limits or source-aware
ranking from the beginning.

For example, retrieval could first select the best chunks from each source and
then apply the final ranking across the combined candidates.

### 7. Treat prompt rules as a safeguard, not the main control mechanism

Some behaviours, such as multilingual fallback responses and repeated-question
echoes, were not fully reliable when controlled only through prompt
instructions.

If starting again, I would keep the prompt simple and implement deterministic
application-level checks for:

- Empty model responses
- Exact question echoing
- Language-aware fallback messages
- Missing retrieval results
- Unsupported requests

This would make system behaviour more predictable.

### 8. Centralize configuration values earlier

Several important parameters were adjusted during testing, including:

- Chunk size and overlap
- OCR spacing thresholds
- Retrieval candidate count
- Maximum LLM context count
- BM25 minimum score
- Model name and context size

If starting again, I would keep all tunable values in a single configuration
module and document their purpose.

This would make experimentation easier and prevent unexplained magic numbers
from appearing in the code.

### Conclusion

The main lesson from the project is that a RAG system should not be treated as
a single model call.

Extraction quality, chunking, retrieval, prompt construction, generation, and
evaluation must be designed and tested as separate components.

The current implementation evolved successfully through testing, but starting
with stronger evaluation, diagnostics, table-aware extraction, and incremental
indexing would have reduced rework and produced a more scalable architecture
earlier.

## Final Reflection

This project evolved from a simple OCR prototype into a complete local
Retrieval-Augmented Generation system supporting multilingual document
question answering, hybrid retrieval, automated evaluation, and a
FastAPI-based web interface.

The most valuable lesson was that building a reliable RAG application is
less about selecting a language model and more about understanding the
interaction between document extraction, retrieval, prompt design,
generation, and evaluation.

Many of the improvements made throughout the project were driven by
systematic testing rather than assumptions. Building an automated
evaluation framework, inspecting retrieval independently from generation,
and documenting failure modes proved just as important as implementing
new features.

Although several limitations remain—particularly for dense tables,
complex OCR layouts, and numeric question answering—the current
implementation provides a solid, extensible foundation for future work
such as incremental indexing, table-aware extraction, reranking, and
improved OCR pipelines.