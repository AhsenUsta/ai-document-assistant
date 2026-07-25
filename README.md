# ai-document-assistant

AI-powered document assistant for PDF, PNG and JPEG question answering.

## Features

- Digital PDF text extraction
- OCR for scanned PDFs
- OCR for PNG and JPG images
- Turkish and English OCR support
- Text chunking with overlap
- Semantic search over document chunks
- RAG-based natural language question answering (local LLM via Ollama)

## Requirements

- Python 3.12+
- Tesseract OCR
- [Ollama](https://ollama.com) installed and running
- The following Ollama model pulled:
```bash
ollama pull qwen3:1.7b
```

**Note:** `TESSERACT_PATH` in `config.py` is set to `"tesseract"`, 
assuming Tesseract is available on your system PATH. If you get a 
"tesseract not found" error, either:
- Add Tesseract to your PATH during/after installation, or
- Set `TESSERACT_PATH` in `config.py` to the full path of your 
  tesseract executable (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe` 
  on Windows, or `/usr/bin/tesseract` on Linux/macOS).

**Note:** `MODEL_NAME` defaults to `qwen3:1.7b` due to VRAM constraints 
on the development machine (4GB GPU). See `DEVLOG.md` for the full 
reasoning. Any locally available Ollama model can be used instead.

## Installation

```bash
pip install -r requirements.txt
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
## Current Stage

The project currently implements:

- PDF text extraction
- OCR for scanned documents (Turkish and English)
- Image OCR (PNG, JPG)
- Text chunking
- Multilingual embeddings
- FAISS vector indexing
- Persistent cache
- Semantic search
- RAG-based question answering via a local LLM (Ollama)

## RAG Pipeline

```text
Documents
    ↓
Text Extraction / OCR
    ↓
Text Chunking
    ↓
Sentence Embeddings
    ↓
FAISS Vector Index
    ↓
Semantic Search
    ↓
Relevant Chunks
    ↓
LLM (Ollama) — Answer Generation
    ↓
Answer
```

## Semantic Search

The semantic search component loads the previously generated FAISS index
and searches for document chunks that are semantically similar to the
user's question.

Run:

```bash
python search.py
```

The application returns:

- similarity score
- source document
- relevant document chunks

## Generated Cache Files

The indexing process generates the following files:

```text
cache/
├── faiss.index
├── chunks.pkl
└── metadata.json
```

## Configuration

The following values can be changed in `config.py`:

```python
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 5
MODEL_NAME = "qwen3:1.7b"
EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-mpnet-base-v2"
)
```

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