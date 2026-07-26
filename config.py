from pathlib import Path


# -------------------------
# PATHS
# -------------------------
BASE_DIR = Path(__file__).parent

DATA_ROOT = BASE_DIR / "data"
CACHE_ROOT = BASE_DIR / "cache"

# -------------------------
# CHUNKING
# -------------------------
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# -------------------------
# OCR
# -------------------------
TESSERACT_PATH = "tesseract"
OCR_LANG = "tur+eng"

# -------------------------
# MODEL
# -------------------------
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
MODEL_NAME = "qwen3:8b"

# -------------------------
# FAISS
# -------------------------
INDEX_PATH = CACHE_ROOT / "faiss.index"
CHUNKS_PATH = CACHE_ROOT / "chunks.pkl"
META_PATH = CACHE_ROOT / "metadata.json"
BM25_PATH = CACHE_ROOT / "bm25.pkl"

# -------------------------
# RETRIEVAL
# -------------------------
TOP_K = 15 # How many candidate chunks to retrieve (retrieval width)
MAX_CONTEXTS = 5 # How many of these will be sent to the LLM?