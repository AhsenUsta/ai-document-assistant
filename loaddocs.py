import re
import time
import pytesseract
import fitz
from PIL import Image
from pathlib import Path
from config import CHUNK_SIZE,CHUNK_OVERLAP,DATA_ROOT,TESSERACT_PATH,OCR_LANG


pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# -------------------------
# HELPERS
# -------------------------
def clean_text(text: str) -> str:
    """Removes excess spaces."""
    return re.sub(r"\s+", " ", text).strip()

# -------------------------
# TEXT EXTRACTORS
# -------------------------
def extract_text_pdf(pdf_path: str | Path) -> str:
    full_text = ""
    t_total_start = time.perf_counter()

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            t_page_start = time.perf_counter()

            if is_scanned_page(page):
                t_ocr_start = time.perf_counter()

                pix = page.get_pixmap(dpi=300, alpha=False)
                img = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                page_text = pytesseract.image_to_string(
                    img,
                    lang=OCR_LANG
                )

                print(
                    f"  [OCR] Page {page_num + 1} -> "
                    f"{time.perf_counter() - t_ocr_start:.2f}s"
                )
            else:
                t_text_start = time.perf_counter()
                page_text = extract_text_from_page(page)

                print(
                    f"  [DIGITAL] Page {page_num + 1} -> "
                    f"{time.perf_counter() - t_text_start:.2f}s"
                )

            full_text += page_text + "\n"

            print(
                f"  [PAGE TOTAL] Page {page_num + 1} -> "
                f"{time.perf_counter() - t_page_start:.2f}s"
            )

    print(
        f"\nPDF total extraction time: "
        f"{time.perf_counter() - t_total_start:.2f}s"
    )

    return full_text.strip()

def extract_text_from_page(page) -> str:
    words = page.get_text("words")
    if not words:
        return ""

    lines = {}
    for w in words:
        y = round(w[1])
        matched = next((k for k in lines if abs(k - y) <= 3), None)
        if matched is not None:
            lines[matched].append(w)
        else:
            lines[y] = [w]

    result = ""
    for y in sorted(lines.keys()):
        row_words = sorted(lines[y], key=lambda x: x[0])
        line_str = ""
        prev_x1 = None

        for w in row_words:
            x0, _, x1, _, text = w[0], w[1], w[2], w[3], w[4]
            if prev_x1 is not None:
                gap = x0 - prev_x1
                if gap > 30:
                    line_str += "\t"
                elif gap > 2:
                    line_str += " "
            line_str += text
            prev_x1 = x1

        result += line_str + "\n"

    return result
    
def extract_text_image(image_path: str | Path) -> str:
    with Image.open(image_path) as img:
        text = pytesseract.image_to_string(
            img,
            lang=OCR_LANG
        )

    return clean_text(text)
    
def is_scanned_page(page) -> bool:
    text = page.get_text("text").strip()
    images = page.get_images(full=True)

    return len(text) < 50 and len(images) > 0

# -------------------------
# CHUNKING
# -------------------------
def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks without cutting words."""
    start_time = time.perf_counter()
    text = clean_text(text)

    if not text:
        return []

    words = text.split()
    chunks: list[str] = []
    current_words: list[str] = []
    current_length = 0

    for word in words:
        added_length = len(word) if not current_words else len(word) + 1

        if current_words and current_length + added_length > chunk_size:
            chunk = " ".join(current_words)
            chunks.append(chunk)

            overlap_words: list[str] = []
            overlap_length = 0

            for previous_word in reversed(current_words):
                word_length = len(previous_word)
                added_overlap = (
                    word_length
                    if not overlap_words
                    else word_length + 1
                )

                if overlap_length + added_overlap > chunk_overlap:
                    break

                overlap_words.insert(0, previous_word)
                overlap_length += added_overlap

            current_words = overlap_words.copy()
            current_length = len(" ".join(current_words))

        added_length = len(word) if not current_words else len(word) + 1
        current_words.append(word)
        current_length += added_length

    if current_words:
        chunks.append(" ".join(current_words))

    print(
        f"[TIMING] split_text ({len(chunks)} chunks): "
        f"{time.perf_counter() - start_time:.3f}s"
    )
    return chunks

# -------------------------
# LOADER
# -------------------------
def load_documents_from_folder(folder_path: str | Path) -> list[dict]:
    _t_total = time.perf_counter()
    chunks: list[dict] = []

    folder = Path(folder_path)

    if not folder.is_dir():
        print(f"Klasör bulunamadı: {folder}")
        return chunks

    skipped = 0

    for full_path in folder.iterdir():
        if not full_path.is_file():
            continue

        _t_file = time.perf_counter()
        extension = full_path.suffix.lower()

        try:
            if extension == ".pdf":
                text = extract_text_pdf(full_path)

            elif extension in {".png", ".jpg", ".jpeg"}:
                text = extract_text_image(full_path)

            else:
                continue

            new_chunks = split_text(text)

            if not new_chunks:
                skipped += 1
                continue

            for chunk in new_chunks:
                chunks.append({
                    "text": chunk,
                    "source": full_path.name,
                })

            print(
                f"[TIMING] file '{full_path.name}' processed: "
                f"{time.perf_counter() - _t_file:.3f}s"
            )

        except Exception as exc:
            print(f"  ✗ Error {full_path.name}: {exc}")

    print(f"\nSkipped (too short / empty): {skipped}")
    print(
        "[TIMING] load_documents_from_folder TOTAL: "
        f"{time.perf_counter() - _t_total:.3f}s"
    )

    return chunks
