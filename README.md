# ai-document-assistant

A multilingual Retrieval-Augmented Generation (RAG) document assistant
for question answering over PDF, PNG, and JPEG documents.

## Features

- Digital PDF text extraction
- OCR for scanned PDFs and images (Turkish and English)
- Text chunking with overlap
- Hybrid retrieval (FAISS semantic search + BM25, combined via
  Reciprocal Rank Fusion)
- RAG-based natural language question answering (local LLM via Ollama)
- Streamlit chat interface with conversation history
- Incremental document indexing (add or remove files without restarting)
- Retrieval debug mode (view sources, retrieved chunks, and similarity scores)
- Automated evaluation harness for measuring retrieval and answer accuracy

## Requirements

- Python 3.12+
- Tesseract OCR
- [Ollama](https://ollama.com) installed and running
- The following Ollama model pulled:
```bash
ollama pull qwen3:8b
```

**Note:** `TESSERACT_PATH` in `config.py` is set to `"tesseract"`, 
assuming Tesseract is available on your system PATH. If you get a 
"tesseract not found" error, either:
- Add Tesseract to your PATH during/after installation, or
- Set `TESSERACT_PATH` in `config.py` to the full path of your 
  tesseract executable (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe` 
  on Windows, or `/usr/bin/tesseract` on Linux/macOS).

**Note:** `MODEL_NAME` defaults to `qwen3:8b`. Earlier iterations used
`qwen3:1.7b` due to VRAM constraints on the development machine (see
`DEVLOG.md` for the full reasoning and trade-offs between model size,
answer quality, and hallucination behavior). Any locally available
Ollama model can be used instead — update `MODEL_NAME` in `config.py`.

## Installation

```bash
pip install -r requirements.txt
ollama pull qwen3:8b
```

## Usage

1. Place your PDF, PNG or JPG files inside the `data/` folder.

Sample test documents are provided in the `test_samples/` folder
   (digital and scanned PDFs/images in Turkish and English, plus a
   financial table and a scanned invoice). To try the system with
   these, copy them into `data/`:

```bash
   cp test_samples/* data/
```

   (On Windows: `copy test_samples\* data\`)
   
2. Build the document index:

```bash
python indexer.py
```

3. Search the indexed documents (retrieval only, no LLM):

```bash
python search.py
```

4. Ask questions and get LLM-generated answers:
```bash
python rag.py

```
### Web interface

```bash
streamlit run app.py
```

Upload documents from the sidebar — they are indexed automatically.
Ask questions in the chat box. Toggle "Show retrieval details" to see
sources, retrieved chunks, and similarity scores for each answer.
Removing a file from the upload list also removes it from the index
and rebuilds the cache.

## RAG Pipeline

```text
Documents
    ↓
Text Extraction / OCR
    ↓
Text Chunking
    ↓
        +----------------------+
        |                      |
        ↓                      ↓
Sentence Embeddings        BM25 Index
        ↓                      ↓
     FAISS Index               │
        └──────────┬───────────┘
                   ↓
      Hybrid Retrieval (RRF)
                   ↓
          Relevant Chunks
                   ↓
            LLM (Ollama)
                   ↓
                Answer
```

## Hybrid Retrieval

The retrieval component loads the previously generated FAISS index and
BM25 index, combines semantic and lexical search using Reciprocal Rank
Fusion (RRF), and returns the most relevant document chunks.

Run:

```bash
python search.py
```

The application returns:

- similarity score (hybrid, semantic, and BM25)
- source document
- relevant document chunks

## Generated Cache Files

The indexing process generates the following files:

```text
cache/
├── faiss.index
├── chunks.pkl
└── metadata.json
└── bm25.pkl
```

## Configuration

The following values can be changed in `config.py`:

```python
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 15
MAX_CONTEXTS = 5
MODEL_NAME = "qwen3:8b"
EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-mpnet-base-v2"
)
```
`TOP_K` and `MAX_CONTEXTS` are deliberately separate: retrieval casts
a wider net (`TOP_K`) to reduce the chance of missing a relevant chunk
ranked lower by either the semantic or lexical scorer, while
`MAX_CONTEXTS` keeps only the top candidates in the LLM's context to
avoid diluting it with lower-relevance chunks.

Hybrid search parameters (BM25/semantic weighting, RRF constants) are
defined in `search.py`'s `hybrid_search` function.

## Test Samples

The `test_samples/` folder contains sample documents used during
development and testing (see `TESTING.md` for detailed test results):

- `digital_tr_product_guide.pdf` — TÜBİTAK founding law/purpose
  document (digital Turkish PDF)
- `digital_en_product_guide.pdf` — EPA Sample and Evidence Management
  SOP (digital English PDF)
- `ocr_tr_production.jpg` / `.png` — COCO dataset description
  (scanned Turkish document, OCR)
- `ocr_en_product_guide.pdf` — Missouri public water systems notice
  letter (scanned English document, OCR)
- `digital_tr_table.pdf` — TÜİK financial statement/balance sheet
  (digital Turkish PDF with dense tabular data)
- `ocr_en_invoice_table.pdf` — sample tax invoice with a multi-column
  table (scanned English document, OCR — used to test table/numeric
  extraction)

These are provided for convenience so the system can be tested without
needing to source your own documents.

## Automated Evaluation

An automated evaluation harness is available to systematically test
retrieval and answer quality:

```bash
python evaluate.py
```

This runs the test cases defined in `evaluation.json` and reports:
- **Source Hit@K** — whether the correct source document was retrieved
- **Answer Accuracy** — whether the generated answer matches the
  expected value or contains the expected keywords

A detailed report is written to `evaluation_report.json`. The current
benchmark consists of 32 automated test cases. See `TESTING.md` for
the latest benchmark results and a discussion of the system's known
limitations.