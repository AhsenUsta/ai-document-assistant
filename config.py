from pathlib import Path


# -------------------------
# PATHS
# -------------------------
BASE_DIR = Path(__file__).parent

DATA_ROOT = BASE_DIR / "data"

# -------------------------
# CHUNKING
# -------------------------
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# -------------------------
# OCR
# -------------------------
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
OCR_LANG = "tur+eng"