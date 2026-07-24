# TESTING

This document describes the tests performed for the document loading and preprocessing stage of the project.

---

## Test 1 – Digital English PDF

**Expected**

- Detect the document as a digital PDF.
- Extract text without using OCR.
- Split the extracted text into chunks.

**Result**

- Passed
- All pages were processed as digital pages.
- Text was extracted successfully.
- 54 chunks were generated.

---

## Test 2 – Digital Turkish PDF

**Expected**

- Extract Turkish text without OCR.
- Preserve Turkish characters.
- Split the extracted text into chunks.

**Result**

- Passed
- Turkish text was extracted successfully.
- Turkish characters were preserved correctly.
- 10 chunks were generated.

---

## Test 3 – Scanned English PDF (OCR)

**Expected**

- Detect scanned pages.
- Extract text using OCR.
- Split the extracted text into chunks.

**Result**

- Passed
- OCR successfully extracted the document text.
- Minor OCR recognition errors were observed.
- 3 chunks were generated.

---

## Test 4 – Turkish PNG (OCR)

**Expected**

- Extract Turkish text using OCR.
- Split the extracted text into chunks.

**Result**

- Passed with minor limitations.
- OCR extracted the main document content successfully.
- Some Turkish characters were recognized incorrectly due to OCR limitations.
- 5 chunks were generated.

---

## Test 5 – Turkish JPG (OCR)

**Expected**

- Extract Turkish text using OCR.
- Split the extracted text into chunks.

**Result**

- Passed with minor limitations.
- OCR extracted the main document content successfully.
- Some Turkish characters were recognized incorrectly due to OCR limitations.
- 5 chunks were generated.

---

## Test 6 – Chunking

**Configuration**

- Chunk size: 600 characters
- Chunk overlap: 100 characters

**Expected**

- Create chunks without splitting words.
- Preserve context using overlap.
- Keep chunk lengths close to the configured size.

**Result**

- Passed
- The chunking algorithm was updated to split text at word boundaries.
- Words are no longer split between chunks.
- Context is preserved through overlapping text.
- Generated chunks remained close to the configured size.

---

## Summary

| Feature | Status |
|---------|--------|
| Digital PDF extraction | ✅ Passed |
| OCR (English) | ✅ Passed |
| OCR (Turkish) | ✅ Passed (minor limitations) |
| PNG support | ✅ Passed |
| JPG support | ✅ Passed |
| Chunk generation | ✅ Passed |
| Word-boundary chunking | ✅ Passed |