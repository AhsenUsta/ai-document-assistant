# ai-document-assistant

AI-powered document assistant for PDF, PNG and JPEG question answering.

## Features

- Digital PDF text extraction
- OCR for scanned PDFs
- OCR for PNG and JPG images
- Turkish and English OCR support
- Text chunking with overlap

## Requirements

- Python 3.12+
- Tesseract OCR

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Place your PDF, PNG or JPG files inside the `data/` folder.

2. Build the document index:

```bash
python indexer.py
```

3. Search the indexed documents:

```bash
python search.py
```

## Current Stage

The project currently implements:

- PDF text extraction
- OCR for scanned documents
- Image OCR
- Text chunking
- Multilingual embeddings
- FAISS vector indexing
- Persistent cache
- Semantic search

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
EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-mpnet-base-v2"
)
```