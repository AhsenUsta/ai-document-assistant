from pathlib import Path
import shutil
import rag
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import CHUNKS_PATH, INDEX_PATH, CACHE_ROOT, DATA_ROOT, STATIC_DIR
from indexer import rebuild_index


BASE_DIR = Path(__file__).resolve().parent

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
}

STATIC_DIR.mkdir(parents=True, exist_ok=True)
DATA_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="AI Document Assistant",
    version="1.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


def cache_is_ready() -> bool:
    """Return True when the FAISS index and chunk cache exist."""
    return INDEX_PATH.exists() and CHUNKS_PATH.exists()


def reload_rag_components() -> None:
    """Reload FAISS, chunks, embedding model and BM25 from disk."""
    success = rag.initialize_components(force_reload=True)

    if success is False:
        raise RuntimeError(
            "Retrieval components could not be initialized."
        )


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail="static/index.html bulunamadı.",
        )

    return HTMLResponse(
        content=index_path.read_text(encoding="utf-8")
    )


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "index_ready": cache_is_ready(),
        "rag_initialized": (
            rag.faiss_index is not None
            and rag.document_chunks is not None
            and rag.bm25 is not None
        ),
    }


@app.post("/documents")
async def upload_documents(
    files: list[UploadFile] = File(...),
) -> dict:
    saved_files: list[str] = []

    try:
        for uploaded_file in files:
            filename = Path(
                uploaded_file.filename or "uploaded_file"
            ).name

            extension = Path(filename).suffix.lower()

            if extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {filename}",
                )

            destination = DATA_ROOT / filename

            content = await uploaded_file.read()
            destination.write_bytes(content)

            saved_files.append(filename)

        # OCR, extraction, chunking, embeddings,
        # FAISS and BM25 operations are blocking.
        index_result = await run_in_threadpool(
            rebuild_index
        )

        if not cache_is_ready():
            raise RuntimeError(
                "The index files could not be created."
            )

        # The old objects in rag.py still point to the previous index.
        # Reload them after every index rebuild.
        await run_in_threadpool(
            reload_rag_components
        )

        return {
            "success": True,
            "uploaded_files": saved_files,
            "indexed_files": index_result["indexed_files"],
            "chunk_count": index_result["chunk_count"],
            "faiss_vectors": index_result["faiss_vectors"],
            "duration": index_result["duration"],
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Upload or indexing failed: {exc}",
        ) from exc

    finally:
        for uploaded_file in files:
            await uploaded_file.close()


@app.post("/ask")
async def ask_question(
    question: str = Form(...),
) -> dict:
    clean_question = question.strip()

    if not clean_question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if not cache_is_ready():
        raise HTTPException(
            status_code=400,
            detail=(
                "No document index is available. "
                "Upload and index documents first."
            ),
        )

    try:
        if (
            rag.faiss_index is None
            or rag.document_chunks is None
            or rag.bm25 is None
        ):
            await run_in_threadpool(
                reload_rag_components
            )

        result = await run_in_threadpool(
            rag.generate_answer,
            clean_question,
        )

        return {
            "question": result.get(
                "question",
                clean_question,
            ),
            "answer": result.get(
                "answer",
                "No answer could be generated.",
            ),
            "sources": result.get(
                "sources",
                [],
            ),
            "results": result.get(
                "results",
                [],
            ),
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Index cache is missing: {exc}",
        ) from exc

    except ConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not connect to Ollama. "
                "Make sure Ollama is running."
            ),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed: {exc}",
        ) from exc

def delete_directory_contents(directory: Path) -> int:
    """
    Deletes every file and folder inside the given directory,
    while preserving the directory itself.
    """
    if not directory.exists():
        return 0

    deleted_count = 0

    for item in directory.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

            deleted_count += 1

        except OSError as exc:
            raise RuntimeError(
                f"Could not delete '{item.name}': {exc}"
            ) from exc

    return deleted_count


@app.delete("/documents/clear")
async def clear_documents():
    try:
        deleted_documents = delete_directory_contents(DATA_ROOT)
        deleted_index_files = delete_directory_contents(CACHE_ROOT)

        # Clear in-memory retrieval components.
        rag.faiss_index = None
        rag.document_chunks = None
        rag.bm25 = None

        return {
            "success": True,
            "message": "All documents and index files were cleared.",
            "deleted_documents": deleted_documents,
            "deleted_index_files": deleted_index_files,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Documents could not be cleared: {exc}",
        ) from exc