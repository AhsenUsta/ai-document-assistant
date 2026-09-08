# AI Document Assistant

![Application Screenshot](docs/images/app.png)

AI Document Assistant is a local Retrieval-Augmented Generation application
that allows users to upload documents and ask natural-language questions about
their content.

The application supports both digital PDFs and scanned documents through OCR.
It combines semantic search and keyword search to retrieve relevant document
sections before generating an answer with a locally running Ollama model.

The final application uses a FastAPI backend and a custom HTML, CSS, and
JavaScript frontend.

## Features

### Document Processing

- Digital PDF extraction
- OCR for scanned PDFs and images
- Turkish and English OCR

### Retrieval

- FAISS semantic search
- BM25 keyword search
- Hybrid retrieval (RRF)
- Multilingual embeddings

### Question Answering

- Local Ollama inference
- Source citations
- Turkish and English queries

### User Interface

- Multiple upload
- Chat interface
- Loading indicators
- Document reset

### Evaluation

- Retrieval diagnostics
- Automated evaluation

## Architecture

```text
Browser
   |
   v
FastAPI
   |
   +-- Document Upload API
   |
   +-- PDF Text Extraction
   |       |
   |       +-- Digital text extraction
   |       |
   |       +-- Tesseract OCR fallback
   |
   +-- Text Chunking
   |
   +-- Embedding Generation
   |
   +-----------------------------+
   |                             |
   v                             v
FAISS Semantic Index         BM25 Index
   |                             |
   +--------------+--------------+
                  |
                  v
      Hybrid Retrieval with RRF
                  |
                  v
          Relevant Chunks
                  |
                  v
          Local Ollama Model
                  |
                  v
              Answer
```

## Example

Upload:
invoice.pdf

Question:
What is the supplier GSTIN?

Answer:
17ABCDEF123GXYZ

Source:
ocr_en_invoice_table.pdf

## Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn
- PyMuPDF
- Tesseract OCR
- Sentence Transformers
- FAISS
- BM25
- Ollama

### Frontend

- HTML
- CSS
- JavaScript

## Requirements

- Python 3.12 or newer
- Tesseract OCR
- Ollama installed and running
- A locally available Ollama model

The default model is:

```bash
ollama pull qwen3:8b
```

### Tesseract configuration

`TESSERACT_PATH` in `config.py` is set to:

```python
TESSERACT_PATH = "tesseract"
```

This assumes that Tesseract is available through the system `PATH`.

When Tesseract is not available in `PATH`, configure its full executable path.

Windows example:

```python
TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
```

Linux example:

```python
TESSERACT_PATH = "/usr/bin/tesseract"
```

### Ollama model configuration

`MODEL_NAME` defaults to:

```python
MODEL_NAME = "qwen3:8b"
```

This model provides the best answer quality but requires more computational resources.

If you are running the project on a lower-end system (e.g. a 4 GB GPU or a CPU-only environment), 
you can switch to a smaller Ollama model by updating `MODEL_NAME` in `config.py`.

Recommended alternatives:

```python
MODEL_NAME = "qwen2.5:3b"
```

or

```python
MODEL_NAME = "llama3.2:3b"
```

Smaller models provide faster inference but may reduce answer quality.

Earlier project iterations used `qwen3:1.7b` because of hardware and VRAM constraints. 
The project now defaults to `qwen3:8b` to improve answer quality.

Additional details about this decision are available in `DEVLOG.md`.

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd ai-document-assistant
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install the Ollama model:

```bash
ollama pull qwen3:8b
```

Make sure Ollama is running before starting the application.

## Running the Application

Start the FastAPI development server:

```bash
uvicorn main:app --reload --port 5000
```

After starting the server, open the following URL in your browser:

```text
http://127.0.0.1:5000
```

## Running with Docker

Start the application and Ollama using Docker Compose:

```bash
docker compose up --build
```

During the first startup, the required Ollama model (`qwen3:8b`) is downloaded automatically.

The application will be available at:

```text
http://127.0.0.1:5000
```

To stop the containers:

```bash
docker compose down
```

## Web Interface Usage

1. Open the application in the browser.
2. Select one or more PDF, PNG, JPG, or JPEG files.
3. Review the selected filenames and file sizes.
4. Click `Upload & Index`.
5. Wait until document processing and index creation are complete.
6. Ask questions about the uploaded documents.
7. Review the generated answer and its source documents.
8. Use `Clear Documents` to remove the current documents and reset the index.

**Note**

While document indexing is running, the question input is disabled to prevent
queries from being executed against an incomplete index.

## Command-Line Usage

The individual pipeline components can also be tested from the command line.

### Build the document index

Place documents inside the configured data directory and run:

```bash
python indexer.py
```

### Test retrieval without the LLM

```bash
python search.py
```

### Test the complete RAG pipeline

```bash
python rag.py
```

### Run automated evaluation

```bash
python evaluate.py
```

## API Endpoints

### Application interface

```http
GET /
```

Returns the HTML application interface.

### Upload and index documents

```http
POST /documents
```

Accepts one or more uploaded files.

The endpoint:

1. validates uploaded files,
2. extracts text (digital or OCR),
3. creates text chunks,
4. generates embeddings,
5. rebuilds the FAISS and BM25 indexes,
6. reloads the in-memory RAG components.

Example response:

```json
{
  "success": true,
  "uploaded_files": [
    "sample.pdf"
  ],
  "indexed_files": [
    "sample.pdf"
  ],
  "chunk_count": 42,
  "faiss_vectors": 42,
  "duration": 4.28
}
```

### Ask a document question

```http
POST /ask
```

Form field:

```text
question
```

Example response:

```json
{
  "question": "What is the IGST amount?",
  "answer": "16,729.92",
  "sources": [
    "ocr_en_invoice_table.pdf"
  ],
  "results": []
}
```

The endpoint returns an error when:

- no question is provided,
- no document index is available,
- document indexing is currently in progress.

**Note**

If no relevant information is found in the indexed documents, 
the endpoint returns a language-aware fallback response instead of an error.

### Clear documents and index

```http
DELETE /documents
```

Removes:

- uploaded documents,
- generated FAISS data,
- serialized chunks,
- BM25 cache data,
- metadata,
- in-memory retrieval state.

This endpoint allows the application to be tested with a clean document set.

### Health check

```http
GET /health
```

Can be used to verify that the FastAPI application is running.

## RAG Pipeline

The question-answering pipeline follows these steps:

```text
User Question
      |
      v
Question Embedding
      |
      +-------------------------+
      |                         |
      v                         v
FAISS Search                BM25 Search
      |                         |
      +------------+------------+
                   |
                   v
     Reciprocal Rank Fusion
                   |
                   v
          Top Retrieved Chunks
                   |
                   v
          Prompt Construction
                   |
                   v
              Ollama
                   |
                   v
               Answer
```

The model is instructed to answer only from the supplied document context.

When the retrieved context does not contain the answer, the application returns
a message indicating that no relevant information was found.

## Hybrid Retrieval

Semantic search and keyword search solve different retrieval problems.

FAISS semantic search is useful for:

- natural-language questions,
- paraphrased questions,
- conceptually similar text,
- multilingual semantic matching.

BM25 is useful for:

- exact labels,
- invoice numbers,
- tax values,
- account names,
- abbreviations,
- document-specific terminology.

The results of both retrievers are combined with Reciprocal Rank Fusion.

This approach improves retrieval for both natural-language questions and exact
field-based questions.

Example questions:

```text
What is the IGST amount?
```

```text
What is the tax amount in words?
```

```text
Proje özel hesabı kaç TL?
```

## Retrieval Configuration

The following values are the project defaults and can be adjusted in
`config.py` to suit different datasets or hardware configurations.

```python
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
CHUNK_STRATEGY = "recursive"

TOP_K = 15
MAX_CONTEXTS = 5

MODEL_NAME = "qwen3:8b"

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-mpnet-base-v2"
)
```

### `CHUNK_SIZE`

Defines the approximate amount of text stored in each document chunk.

### `CHUNK_OVERLAP`

Repeats a portion of the previous chunk to reduce information loss at chunk
boundaries.

### `CHUNK_STRATEGY`

Defines how extracted document text is divided into chunks.

The current default is recursive, which attempts to preserve document
structure by preferring paragraph, line, sentence, and word boundaries before
falling back to character-level splitting.

Fixed-size chunking is also available for comparison and experimentation.

### `TOP_K`

Defines how many candidate chunks are collected by the retrieval pipeline.

### `MAX_CONTEXTS`

Defines how many of the highest-ranked chunks are passed to the LLM.

`TOP_K` and `MAX_CONTEXTS` are intentionally separate.

Retrieval uses a wider candidate set to reduce the chance of missing a relevant
chunk. The LLM receives a smaller set to avoid context dilution and unnecessary
generation latency.

Additional hybrid retrieval parameters, including Reciprocal Rank Fusion (RRF),
are implemented in `search.py`.

## OCR Processing

Digital PDFs are first processed with PyMuPDF.

When a page contains little or no usable embedded text, the page is rendered as
an image and processed with Tesseract OCR.

Supported OCR languages include:

```text
Turkish
English
```

OCR quality depends on:

- scan resolution,
- image sharpness,
- page rotation,
- table complexity,
- font quality,
- document layout.

Labels may sometimes be extracted differently from their original form.

For example:

```text
GSTIN/UIN
GSTIN / UIN
GSTIN|UIN
GSTIN/UlN
```

These OCR variations can affect exact keyword matching.

## Generated Cache Files

The indexing process generates the following files:

```text
cache/
├── faiss.index
├── chunks.pkl
├── metadata.json
└── bm25.pkl
```

### `faiss.index`

Stores the semantic vector index.

### `chunks.pkl`

Stores the extracted document chunks and source metadata.

### `metadata.json`

Stores index-related metadata.

### `bm25.pkl`

Stores the keyword retrieval index.

These files are regenerated whenever the document index is rebuilt or reset.

## Project Structure

```text
ai-document-assistant/
├── main.py
├── indexer.py
├── search.py
├── rag.py
├── evaluate.py
├── config.py
├── requirements.txt
├── evaluation.json
├── README.md
├── TESTING.md
├── DEVLOG.md
├── data/
├── cache/
├── test_samples/
└── docs
	└── images
		└── app.png
└── static/
    ├── index.html
    ├── app.js
    └── style.css
```

## Test Samples

The `test_samples/` directory contains documents used during development, 
testing and evaluation.

These sample documents are included to demonstrate OCR, retrieval, and
question-answering across different document types and languages.

### Digital Turkish document

```text
digital_tr_product_guide.pdf
```

A Turkish digital PDF used to evaluate text extraction and Turkish retrieval.

### Digital English document

```text
digital_en_product_guide.pdf
```

An English digital PDF used to evaluate semantic and keyword retrieval.

### Turkish OCR samples

```text
ocr_tr_production.jpg
ocr_tr_production.png
```

Scanned Turkish documents used to test image OCR.

### English OCR document

```text
ocr_en_product_guide.pdf
```

A scanned English PDF used to evaluate OCR and English question answering.

### Turkish financial table

```text
digital_tr_table.pdf
```

A digital PDF containing dense financial and tabular information.

Example question:

```text
Proje özel hesabı kaç TL?
```

### English invoice table

```text
ocr_en_invoice_table.pdf
```

A scanned invoice containing numeric values, labels, and multi-column table
content.

Example questions:

```text
What is the IGST amount?
```

```text
What is the tax amount in words?
```

Detailed evaluation results, test cases, and known limitations are documented
in `TESTING.md`.

## Automated Evaluation

The project includes an automated evaluation framework for measuring
retrieval and question-answering performance.

Run:

```bash
python evaluate.py
```

Test cases are defined in:

```text
evaluation.json
```

The evaluation process measures:

- Source Hit@K
- Expected source retrieval
- Answer accuracy
- Expected keyword matching
- Exact numeric answer matching

The generated evaluation report is written to:

```text
evaluation_report.json
```

The current benchmark contains 32 automated test cases.

### Chunking Evaluation

Fixed and recursive chunking strategies were evaluated using the same
32-question benchmark.

| Strategy            | Answer Accuracy | Source Accuracy | Avg. Response Time |
| ------------------- | --------------: | --------------: | -----------------: |
| Fixed (900/150)     |           62.5% |            100% |            8.759 s |
| Recursive (900/150) |       **75.0%** |          96.43% |        **8.681 s** |

Recursive chunking was selected as the default strategy because it improved
answer accuracy by 12.5 percentage points while maintaining approximately the
same average response time.

Detailed experiment results and remaining OCR/table-related limitations are
documented in `TESTING.md`.

## Manual Testing Scenarios

The application was manually tested using:

- digital Turkish PDFs,
- digital English PDFs,
- scanned Turkish images,
- scanned English PDFs,
- financial tables,
- invoice tables,
- multiple simultaneous document uploads,
- missing-answer questions,
- Turkish questions,
- English questions,
- document deletion and index reset,
- questions submitted during index rebuilding,
- unsupported and empty uploads.

## Known Limitations

- OCR accuracy depends on the quality of the source document.
- Complex tables may not preserve their original row and column structure.
- Multi-column PDFs may produce imperfect reading order.
- A label and its value may be separated across neighboring chunks.
- Exact values can be missed when OCR changes punctuation or characters.
- Repeated labels may produce ambiguous answers.
- The first request may take longer while models are loaded.
- Index rebuilding is currently performed as a blocking background operation.
- The current implementation is intended for local, single-user use.
- Authentication and authorization are not included.
- Conversation history is not persisted after a page refresh.
- The application is not designed as a production multi-user deployment.

## Development History

The first working prototype used Streamlit to validate:

- document upload,
- OCR,
- hybrid retrieval,
- RAG generation,
- source display,
- retrieval debugging.

The application was later migrated to FastAPI with a custom frontend to provide:

- clearer frontend and backend separation,
- explicit API endpoints,
- better loading-state control,
- better error handling,
- document selection display,
- index reset functionality,
- protection against concurrent indexing and querying,
- a more production-like case-study architecture.

The final version contains one web interface based on FastAPI.

A detailed development history and the reasoning behind technical decisions are
available in `DEVLOG.md`.

## Future Improvements

- Incremental document indexing
- Per-document deletion
- Background task queue for indexing
- Real-time OCR and indexing progress
- Layout-aware text extraction
- Table-specific extraction
- Neighboring chunk expansion
- Reranking model
- Metadata filters
- Document-level search filters
- Improved query normalization
- Exact-label boosting
- Persistent chat history
- Authentication
- Multi-user index isolation
- Production database integration
- Docker support
- Automated browser tests

## Documentation

- **TESTING.md** – Manual test cases, automated evaluation results, edge cases, and known limitations.
- **DEVLOG.md** – Development phases, architectural decisions, challenges, and technical trade-offs.

## License

This project was developed as a technical case study and is provided under the MIT License.
See the `LICENSE` file for details.