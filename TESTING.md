# TESTING

This document describes the testing performed for the document loading,
retrieval, and question-answering pipeline of the project.

---

## Test Environment

- Embedding model:
  `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- Retrieval:
  Hybrid Search (Semantic + BM25 using Reciprocal Rank Fusion)
- LLM:
  qwen3:8b (Ollama)
- OCR:
  Tesseract OCR
- Evaluation:
  32 automated benchmark questions
  
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

**Document:** `ocr_en_product_guide.pdf` — a scanned 8-page public
notice letter (Missouri Department of Health and Senior Services,
public water systems bacteriology testing update), including a sample
collection form and instructional diagrams.

**Expected**

- Detect scanned pages.
- Extract text using OCR.
- Split the extracted text into chunks.

**Result**

- Passed
- All 8 pages were correctly detected as scanned and processed via OCR.
- Text was extracted successfully, including tables and instructional
  content with embedded diagrams.
- 49 chunks were generated.

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

## Semantic Search Tests

### Environment

- Embedding model:
  `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- Embedding dimension: `768`
- Number of indexed chunks: `136`
- Default `TOP_K`: `15` (candidate retrieval)
- `MAX_CONTEXTS`: `5` (contexts passed to the LLM)
- Search engine: `FAISS`
- Similarity method: cosine similarity through normalized vectors

### Test 1 – Turkish document retrieval

**Description**

Verified that a Turkish query successfully retrieved relevant chunks from
a Turkish document.

**Status**

Passed

### Test 2 – English document retrieval

**Description**

Verified that an English query correctly retrieves relevant chunks from an
English document.

**Status**

Passed

### Test 3 – Persistent Cache

**Description**

Verified that the FAISS index and cached chunks were loaded successfully
without rebuilding embeddings.

**Status**

Passed

### Test 4 – Cross-language retrieval (English → Turkish)

**Description**

Verified that an English query successfully retrieved relevant
information from a Turkish OCR document.

**Status**

Passed


## RAG / Question-Answering Tests

### Environment
- LLM: `qwen3:8b` (via Ollama)
- `num_ctx`: 2048
- `temperature`: 0.1

### Test 1 – COCO Question Retrieval (Turkish)
**Description**
Verified that a Turkish question about the COCO dataset returns a
correct, source-grounded answer. Note: despite the original intent to
test a "digital" document here, the COCO content was later confirmed
to reside only in the OCR'd `ocr_tr_production.jpg`/`.png` files (see
TÜBİTAK/EPA SOP file mislabeling note below) — so this test actually
exercises OCR'd Turkish text retrieval, not digital PDF retrieval.

**Query:** "COCO veri seti nedir?"

**Status**
Passed

---

### Test 2 – COCO Question Retrieval (English)
**Description**
Verified that an English question about the COCO dataset returns a
correct, source-grounded answer. As with Test 1, this content is
sourced from the OCR'd `ocr_tr_production.jpg`/`.png` files, which
contain a mixed Turkish/English passage — not from a separate digital
English document.

**Query:** "What is the COCO dataset used for?"

**Status**
Passed

---

### Test 3 – Cross-document Retrieval
**Description**
Verified that questions about different documents (TÜBİTAK and EPA SOP)
in the same session return correct, non-mixed answers.

**Queries:**
- "TÜBİTAK'ın kuruluş amacı nedir?"
- "Sample custody nasıl sağlanır?"

**Status**
Passed

**Observation**
The assistant now consistently answers in the language of the user's
question, even when the retrieved document is written in another
language. This behavior is enforced through language detection and
post-generation fallback normalization.

---

### Test 4 – Cross-language Retrieval (EN question → TR document)
**Description**
Verified that an English question can retrieve and correctly answer
from a Turkish-language document, confirming the multilingual embedding
model works as intended.

**Query:** "What is TÜBİTAK's purpose?"

**Status**
Passed

---

### Test 5 – Retrieval Success, Generation Failure (Known Limitation)
**Description**
Tested whether the system correctly answers a question whose answer
exists in the documents but is buried in OCR-degraded text.

**Query:** "COCO kaç görüntü içeriyor?"

**Retrieval result:** Passed — the correct chunk (containing "330K
gériinti igerir") was retrieved with a similarity score of 0.57–0.58,
confirmed via direct inspection using `search.py`.

**Generation result:** Failed — the LLM consistently (reproduced 3+
times) responded "I could not find the answer in the provided
documents," despite the correct information being present in context.

**Root cause analysis:**
- Retrieval was verified correct by bypassing the LLM and inspecting
  raw search results.
- The failure is isolated to the generation step.
- Likely cause: OCR-degraded text (e.g., "tizere", "gériinti") reduces
  the small model's (qwen3:1.7b) confidence in extracting the correct
  number, causing it to default to the "not found" fallback defined in
  the prompt.
- Additional testing with qwen3:8b showed that a larger model improves
some OCR-related extraction failures, although generation failures can
still occur when OCR quality is severely degraded.

**Status**
Known limitation — documented, not resolved in this iteration.
Potential future fixes: OCR post-processing/cleanup, duplicate chunk
deduplication, or prompt adjustments for handling degraded context.

---
### Test 6 – Hallucination Check
**Description**
Verified that the system does not fabricate an answer when the
requested information does not exist in any document.

**Query:** "COCO veri setinin lisans ücreti nedir?"

**Answer:** The assistant returned the language-appropriate "not found" message.

**Status**
Passed — the system correctly avoided hallucinating a fabricated
answer for information not present in any indexed document.

---

### Test 7 – Numeric Extraction from Financial Table (TR)
**Description**
Tested whether the system correctly extracts a specific figure from a
dense financial statement table (TÜİK balance sheet).

**Query:** "TÜİK'in 2022 yılı aktif toplamı ne kadar?"

**Expected answer:** 377.527.395,96 TL (explicitly labeled "AKTİF
TOPLAMI" in the source table)

**Actual answer:** "760.049,74 TL" — an incorrect figure taken from an
unrelated line in the same table.

**Status**
Failed — hallucination. The model returned a plausible-looking but
incorrect number rather than the correct total or a "not found"
response.

---

### Test 8 – Numeric Extraction with Fabricated Reasoning (TR)
**Description**
Tested extraction of a specific expense figure from the same financial
table.

**Query:** "Personel giderleri ne kadardır?"

**Expected answer:** 612.828.211,01 (explicitly labeled "Personel
Giderleri" in the source table)

**Actual answer:** The model ignored the correct figure entirely,
invented an unrelated formula ("Personel Giderleri = Gelirler Toplamı
- Giderler Toplamı + İndirim"), and computed a fabricated negative
result (-5.871.294,26).

**Status**
Failed — severe hallucination. This is a more serious failure mode
than a false "not found," because the model presented a fabricated
number along with invented, confident-sounding reasoning.

---

### Test 9 – OCR Extraction Failure on Complex Table Layout
**Description**
Tested whether the system can extract the grand total from a scanned
invoice with a multi-section table layout (line items + summary/tax
breakdown area).

**Query:** "What is the total amount on the invoice?"

**Expected answer:** ₹1,56,146.00 (labeled "Total" at the bottom of
the invoice)

**Investigation:**
1. `search.py` was run with `TOP_K` temporarily increased from 5 to
   10 — the correct figure still did not appear in any retrieved
   chunk.
2. The raw cached chunks for this document were inspected directly
   (bypassing both retrieval and generation). Only 2 chunks were
   generated for the entire invoice, and neither contains the grand
   total, total quantity ("298 PCS"), the amount-in-words line, or the
   HSN/SAC tax summary table at the bottom of the invoice.

**Root cause:** This is an OCR extraction failure, not a retrieval or
generation issue — Tesseract did not read the invoice's dense,
multi-column bottom summary section into the extracted text at all,
so the information was never available to be chunked, retrieved, or
answered from.

**Status**
Known limitation — complex, multi-section table layouts (particularly
overlapping summary/total box structures) are not reliably captured
by the current OCR + line-reconstruction pipeline in `loaddocs.py`.
This is distinct from Test 5 (a generation-level failure with correct
retrieval) — this is purely an extraction-level gap.

---

### Test 10 – Additional Invoice Query Results
**Description**
Further queries against the same scanned invoice, to characterize
failure patterns.

| Query | Expected | Actual | Failure Type |
|---|---|---|---|
| "How many product line items are listed?" | 5 | 0, with fabricated reasoning that the documents only contain chain-of-custody/financial records | Hallucination |
| "What is the supplier's GSTIN number?" | 17ABCDEF123GXYZ (present in the retrieved chunk) | "Not found" | False negative |
| "What is the IGST tax rate applied?" | 12% | 12% | Passed |
| "What is the payment due date?" | Not present in the document | "Not found" | Passed (correct rejection) |

**Status**
Mixed — the system handles simple, single-fact lookups reasonably
(IGST rate, correctly absent due date) but is unreliable for
enumeration ("how many items") and can hallucinate answers for facts
that were actually present but perhaps not attended to correctly
(GSTIN number).

---

### Test 11 – Hybrid Search Implementation (BM25 + Semantic)

**Motivation**
Tests 7-10 suggested that pure semantic search sometimes failed to
rank the correct chunk highly enough, especially for queries involving
specific codes/terms (e.g., "IGST") in short, code-heavy documents like
the invoice. Implemented hybrid search combining BM25 (lexical) and
semantic search via Reciprocal Rank Fusion (RRF).

**Initial regression:** The first implementation used raw BM25 rank
without a minimum score threshold, causing chunks with near-zero
lexical relevance (e.g., an unrelated TÜBİTAK document sharing common
words like "Türkiye" or "kurum") to enter the fused ranking. This
caused two previously-correct answers to break:
- "TÜİK aktif toplamı nedir?" → wrong figure returned
- "Personel giderleri ne kadardır?" → reverted to "not found"

**Fix:** Added a `bm25_min_score` threshold to exclude near-zero
lexical matches from the fused ranking, preventing low-relevance
documents from polluting results.

**Status**
Fixed after regression — see Test 12 for before/after comparison.

---

### Test 12 – Prompt Refinement: Label-Value Matching

**Motivation**
Even after fixing the hybrid search regression, "TÜİK aktif toplamı
nedir?" returned the wrong number (-760.049,74 instead of
377.527.395,96). Root cause: OCR/table-flattening produces
"value label value label" ordering (e.g.,
"-760.049,74 AKTİF TOPLAMI 377.527.395,96"), and the model was
matching the number preceding the label instead of following it.

**Fix:** Added explicit prompt rules instructing the model to match
the number immediately following a label (not preceding it), and to
double-check when multiple similar/paired labels appear near each
other (e.g., paired totals like active/passive, income/expense).

**Results (before → after):**

| Query | Before | After |
|---|---|---|
| "TÜİK aktif toplamı nedir?" | Wrong figure (-760.049,74) | Correct (377.527.395,96) |
| "Personel giderleri ne kadardır?" | Correct, but the answer chunk ranked last (5th) among mostly irrelevant retrieval results | Correct |
| "What is the supplier GSTIN?" | "Not found," despite the correct value being present in the top-ranked chunk (a generation-level disambiguation failure — three similar GSTIN/UIN codes appear in the same chunk) | Correct (17ABCDEF123GXYZ) |
| "What is the IGST rate?" | Retrieval failed entirely (invoice not retrieved for this specific phrasing) | Correct (12%), invoice retrieved at rank 1 |
| "COCO veri setinin lisans ücreti nedir?" | English fallback | Language-aware fallback |

**Status**
Passed — prompt refinement, combined with the hybrid search fix,
resolved all four previously-failing queries above.

---

## Test 13 – Expanded Automated Evaluation

### Motivation

After validating the evaluation framework on an initial benchmark,
the benchmark was expanded to better measure retrieval, answer quality,
and hallucination handling across different document types.

### Test Set

The benchmark consists of **32 questions** covering:

- OCR invoice
- COCO documentation
- TÜBİTAK documentation
- EPA SOP
- Deliberate "not found" questions

Questions include:

- Fact retrieval
- Semantic understanding
- Numeric extraction
- Hallucination detection

### Metrics

- Overall Accuracy
- Answer Accuracy
- Source Hit@K

### Results

| Metric | Result |
|--------|--------|
| Total tests | 32 |
| Overall Accuracy | 68.75% |
| Answer Accuracy | 68.75% |
| Source Hit@K | 96.30% |
| Errors | 1 |

### Analysis

The evaluation highlights a clear distinction between retrieval quality
and answer generation quality.

Retrieval performed consistently, achieving **96.30% Source Hit@K**,
indicating that the hybrid retrieval pipeline usually selected the
correct source document.

Most failures occurred during answer generation rather than retrieval.

The main failure patterns were:

- OCR extraction limitations in complex invoice layouts.
- Failure to extract specific fields despite correct retrieval.
- Strict keyword matching (e.g., synonymous wording such as
  "bölütleme" instead of "segmentasyon").
- One runtime CUDA/Ollama error unrelated to the retrieval pipeline.

The benchmark also confirmed that multilingual fallback handling works
correctly. All deliberate "not found" questions returned the
language-appropriate fallback message without hallucinating answers.

### Conclusion

The evaluation demonstrates that retrieval is largely reliable, while
remaining weaknesses are concentrated in OCR quality and answer
generation for complex structured documents rather than document
selection itself.

---

### Test 14 – Incremental Document Indexing

**Description**

Verified that newly uploaded documents are indexed automatically and
that removing a document updates the retrieval index accordingly.

**Procedure**

1. Upload Document A and verify it can be queried.
2. Upload Document B and verify both documents are retrievable.
3. Remove Document A.
4. Verify that answers are generated only from Document B.

**Status**

Passed

---

### Test 15 – Streamlit Conversation History

**Description**

Verified that the chat interface preserves conversation history during
a session and correctly clears it when requested.

**Procedure**

1. Ask multiple questions.
2. Verify previous messages remain visible.
3. Click **Clear conversation**.
4. Verify the conversation history is removed.

**Status**

Passed

---

### Test 16 – Language-Aware Fallback Responses

**Description**

Verified that the assistant returns the fallback message in the same
language as the user's question when the requested information is not
present in the indexed documents.

**Procedure**

| Query | Expected |
|--------|----------|
| Turkish question with no matching information | Turkish fallback message |
| English question with no matching information | English fallback message |

**Status**

Passed

**Observation**

The fallback language is determined consistently through language
detection and post-generation normalization, independent of the
language of the retrieved documents.

---

### Test 17 – Retrieval Debug Information

**Description**

Verified that enabling retrieval debug mode displays the retrieved
chunks, source documents, and retrieval scores without affecting the
generated answer. This mode is intended for development and evaluation 
rather than end-user usage.

**Status**

Passed

---

## Summary of RAG/QA Limitations

Testing across financial tables and a scanned invoice surfaced four
distinct failure modes, in increasing order of severity:

1. **False negatives** (Tests 5, 10) — correct information is present
   in retrieved context, but the model responds "not found."
2. **OCR extraction gaps** (Test 9) — dense, multi-section table
   layouts are not fully captured during text extraction, so
   information is unavailable before retrieval even begins.
3. **Hallucination** (Tests 7, 8, 10) — the model fabricates plausible
   but incorrect numbers, sometimes with invented reasoning/formulas,
   rather than declining to answer.
4. **Structured-document extraction limitations** (Tests 9) — invoice
   fields located in dense table layouts are sometimes not extracted
   correctly, preventing successful retrieval and answer generation.

These findings indicate that while the system performs reliably for
narrative/descriptive text (Tests 1–4, 6), numeric extraction from
dense tabular data is not currently reliable and would need dedicated
handling (see `DEVLOG.md` for the scope decision on this) before being
used for financial or invoice-processing use cases in production.

Overall, the system performs reliably on multilingual document
retrieval and general question answering.

The remaining limitations are concentrated in three areas:

- OCR quality for dense tables
- Retrieval balance for highly imbalanced corpora
- Numeric reasoning over partially extracted tables

These limitations are documented throughout this report and provide a
clear roadmap for future improvements.