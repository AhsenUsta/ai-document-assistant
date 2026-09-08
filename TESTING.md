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

## TC-001 — Digital English PDF Extraction

**Input**

- Document: `digital_en_product_guide.pdf`

**Expected**

- Detect the document as a digital PDF.
- Extract text without using OCR.
- Split the extracted text into chunks.

**Result**

- All pages were processed as digital pages.
- Text was extracted successfully.
- 54 chunks were generated.

**Status**

- ✅ Passed

---

## TC-002 — Digital Turkish PDF Extraction

**Input**

- Document: `digital_tr_product_guide.pdf`

**Expected**

- Extract Turkish text without OCR.
- Preserve Turkish characters.
- Split the extracted text into chunks.

**Result**

- Turkish text was extracted successfully.
- Turkish characters were preserved correctly.
- 10 chunks were generated.

**Status**

- ✅ Passed

---

## TC-003 – Scanned English PDF (OCR)

**Input** 

- Document: `ocr_en_product_guide.pdf` 
- Type: Scanned PDF (8 pages)

**Expected**

- Detect scanned pages.
- Extract text using OCR.
- Split the extracted text into chunks.

**Result**

- All 8 pages were correctly detected as scanned and processed via OCR.
- Text was extracted successfully, including tables and instructional
  content with embedded diagrams.
- 49 chunks were generated.

**Status**

- ✅ Passed

---

## TC-004 – Turkish PNG (OCR)

**Input**

- Document: `ocr_tr_product_guide.png`

**Expected**

- Extract Turkish text using OCR.
- Split the extracted text into chunks.

**Result**

- OCR extracted the main document content successfully.
- Some Turkish characters were recognized incorrectly due to OCR limitations.
- 5 chunks were generated.

**Status**

- ✅ Passed with minor limitations

---

## TC-005 – Turkish JPG (OCR)

**Input**

- Document: `ocr_tr_production.jpg`

**Expected**

- Extract Turkish text using OCR.
- Split the extracted text into chunks.

**Result**

- OCR extracted the main document content successfully.
- Some Turkish characters were recognized incorrectly due to OCR limitations.
- 5 chunks were generated.

**Status**

- ✅ Passed with minor limitations

---

## TC-006 – Chunk Generation

**Configuration**

- Chunk size: 600 characters
- Chunk overlap: 100 characters

**Expected**

- Create chunks without splitting words.
- Preserve context using overlap.
- Keep chunk lengths close to the configured size.

**Result**

- The chunking algorithm was updated to split text at word boundaries.
- Words are no longer split between chunks.
- Context is preserved through overlapping text.
- Generated chunks remained close to the configured size.

**Status**

- ✅ Passed 

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
- Number of indexed chunks: `140`
- Default `TOP_K`: `15` (candidate retrieval)
- `MAX_CONTEXTS`: `5` (contexts passed to the LLM)
- Search engine: `FAISS`
- FAISS index type: `IndexFlatIP`
- Similarity method: cosine similarity through normalized vectors

### TC-007 – Turkish Semantic Search

**Description**

Verified that a Turkish query successfully retrieved relevant chunks from
a Turkish document.

**Status**

- ✅ Passed 

###  TC-008 – English Semantic Search

**Description**

Relevant English chunks were successfully retrieved.
Retrieved contexts matched the semantic meaning of the query.

**Status**

- ✅ Passed 

### TC-009 – Persistent Cache

**Description**

Verified that the FAISS index and cached chunks were loaded successfully
without rebuilding embeddings.

**Status**

- ✅ Passed 

### TC-010 – Cross-language Retrieval (English → Turkish)

**Input**

- Query: "What is TÜBİTAK’s purpose?"
- Document: `ocr_tr_product_guide.pdf`

**Description**

Verified that an English query successfully retrieved relevant
information from a Turkish OCR document.

**Status**

- ✅ Passed 


## RAG / Question-Answering Tests

### Environment

- LLM: `qwen3:8b` (via Ollama)
- `num_ctx`: 2048
- `temperature`: 0.1

### TC-011 – COCO Question Retrieval (Turkish)

**Input**

- Query: "COCO veri seti nedir?"
- Document: `ocr_tr_production.jpg`

**Description**

Verified that a Turkish question about the COCO dataset returns a
correct, source-grounded answer. 

**Note**

Although this test was originally intended for a digital document, the
COCO content was later confirmed to exist only in the OCR-generated
`ocr_tr_production.jpg` / `.png` files. Therefore, this test validates
OCR-based Turkish document retrieval rather than digital PDF retrieval.

**Status**

- ✅ Passed 

---

### TC-012 – COCO Question Retrieval (English)

**Input**

- Query: "What is the COCO dataset used for?"
- Document: `ocr_tr_production.jpg`

**Description**

Verified that an English question about the COCO dataset returns a
correct, source-grounded answer. As with Test 1, this content is
sourced from the OCR'd `ocr_tr_production.jpg`/`.png` files, which
contain a mixed Turkish/English passage — not from a separate digital
English document.

**Status**

- ✅ Passed 

---

### TC-013 – Cross-document Retrieval

**Input**

- Queries:
  - "TÜBİTAK'ın kuruluş amacı nedir?" 
  - "Sample custody nasıl sağlanır?"
  
- Documents: 
  - `ocr_tr_production.jpg`
  - `digital_en_product_guide.pdf`

**Description**

Verified that questions about different documents (TÜBİTAK and EPA SOP)
in the same session return correct, non-mixed answers.

**Status**

- ✅ Passed 

**Observation**

The assistant now consistently answers in the language of the user's
question, even when the retrieved document is written in another
language. This behavior is enforced through language detection and
post-generation fallback normalization.

---

### TC-014 – Cross-language Retrieval (EN question → TR document)

**Input**

- Query: "What is TÜBİTAK's purpose?"
- Document: `digital_tr_product_guide.pdf`

**Description**

Verified that an English question can retrieve and correctly answer
from a Turkish-language document, confirming the multilingual embedding
model works as intended.

**Status**

- ✅ Passed 

---

### TC-015 – Retrieval Success, Generation Failure (Known Limitation)

**Input**

- Query: "COCO kaç görüntü içeriyor?"
- Document: `ocr_tr_production.png`

**Description**
Tested whether the system correctly answers a question whose answer
exists in the documents but is buried in OCR-degraded text.

**Retrieval result:** 

- ✅ Passed — the correct chunk (containing "330K
gériinti igerir") was retrieved with a similarity score of 0.57–0.58,
confirmed via direct inspection using `search.py`.

**Generation result:** 

- ❌ Failed — the LLM consistently (reproduced 3+
times) responded "I could not find the answer in the provided
documents," despite the correct information being present in context.

**Root cause analysis:**

- Retrieval was verified correct by bypassing the LLM and inspecting
  raw search results.
- The failure is isolated to the generation step.
- Likely cause: The issue was originally reproduced with `qwen3:1.7b`, where OCR-degraded
text reduced the model's confidence in extracting the correct number.
Additional testing with `qwen3:8b` showed improved extraction, although
generation failures can still occur when OCR quality is severely degraded.
- Additional testing with qwen3:8b showed that a larger model improves
some OCR-related extraction failures, although generation failures can
still occur when OCR quality is severely degraded.

**Status**

- ⚠️ Known limitation

**Potential future improvements**

- OCR post-processing / cleanup
- Duplicate chunk deduplication
- Prompt adjustments for degraded OCR context

---
### TC-016 – Hallucination Check

**Input**

- Query: "COCO veri setinin lisans ücreti nedir?"
- Document: `digital_en_product_guide.pdf`

**Description**

Verified that the system does not fabricate an answer when the
requested information does not exist in any document.

**Result:** 

The assistant returned the language-appropriate "not found" message.

**Status**

- ✅ Passed — the system correctly avoided hallucinating a fabricated
answer for information not present in any indexed document.

---

### TC-017 – Numeric Extraction from Financial Table (TR)

**Input**

- Query: "TÜİK'in 2022 yılı aktif toplamı ne kadar?"
- Document: `digital_tr_table.pdf`

**Description**

Tested whether the system correctly extracts a specific figure from a
dense financial statement table (TÜİK balance sheet).

**Expected answer**

377.527.395,96 TL (explicitly labeled "AKTİF TOPLAMI" in the source table)

**Actual result**

The assistant returned the language-appropriate "not found" message,
despite the correct value being present in the document.

**Status**

- ❌ Failed

**Observation**

The current system produces a false negative rather than hallucinating
an incorrect value. While this behavior is safer than returning an
invented number, it still fails to extract the required information.

---

### TC-018 – Numeric Extraction with Fabricated Reasoning (TR)

**Input**

- Query: "Personel giderleri ne kadardır?"
- Document: `digital_tr_table.pdf`

**Description**

Tested whether the system correctly extracts the personnel expenses from
a financial statement table.

**Expected answer:** 

612.828.211,01 (explicitly labeled "Personel Giderleri" in the source table)

**Actual answer:** 

612.828.211,01

**Status**

- ✅ Passed

---

### TC-019 – OCR Extraction Failure on Complex Table Layout

**Input**

- Query: "What is the total amount on the invoice?"
- Document: `ocr_en_invoice_table.pdf`

**Description**

Tested whether the system can extract the grand total from a scanned
invoice with a multi-section table layout (line items + summary/tax
breakdown area).

**Expected answer:** 

₹1,56,146.00 (labeled "Total" at the bottom of the invoice)

**Result**

The invoice document was successfully retrieved, but the expected grand
total was not present in the extracted text.

**Investigation**

1. `search.py` confirmed that `ocr_en_invoice_table.pdf` was retrieved as
   the top-ranked document.
2. Inspection of the retrieved chunks showed that the OCR output
   contained invoice metadata, tax information, and line-item values,
   but the grand total (`₹1,56,146.00`) was missing.
3. As a result, the missing value could not be retrieved or generated.

**Root cause**

This is an OCR extraction failure rather than a retrieval or generation
failure. The invoice document is retrieved correctly, but the OCR
pipeline fails to extract the grand total from the complex bottom
summary section.

**Status**

- ⚠️ Known limitation 

This issue is distinct from **TC-015 – Retrieval Success, Generation
Failure**. In TC-015, retrieval succeeded but generation failed. Here,
the required information is never extracted during OCR, making it
unavailable for retrieval and answer generation.

---

### TC-020 – Additional Invoice Query Results

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

- ⚠️ Mixed 

The system handles simple, single-fact lookups reasonably well (e.g.,
IGST rate) and correctly rejects queries for information that is not
present (e.g., payment due date). However, it remains unreliable for
enumeration tasks (e.g., counting product line items) and may produce
false negatives for information that is present in the retrieved
context (e.g., the supplier's GSTIN).

---

### TC-021 – Hybrid Search Implementation (BM25 + Semantic)

**Motivation**

Earlier test cases (TC-017 to TC-020) suggested that pure semantic
search sometimes failed to rank the correct chunk highly enough, 
especially for queries involving specific codes/terms (e.g., "IGST") 
in short, code-heavy documents like the invoice. Implemented hybrid 
search combining BM25 (lexical) and semantic search via Reciprocal Rank Fusion (RRF).

**Initial regression:** 

The first implementation used raw BM25 rank
without a minimum score threshold, causing chunks with near-zero
lexical relevance (e.g., an unrelated TÜBİTAK document sharing common
words like "Türkiye" or "kurum") to enter the fused ranking. This
caused two previously-correct answers to break:
- "TÜİK aktif toplamı nedir?" → wrong figure returned
- "Personel giderleri ne kadardır?" → reverted to "not found"

**Fix:**

Introduced a `bm25_min_score` threshold to filter out near-zero lexical
matches before fusion, preventing unrelated documents from influencing
the final ranking.

**Status**

- ✅ Fixed after regression

See TC-022 for the before/after evaluation.

---

### TC-022 – Prompt Refinement: Label-Value Matching

**Motivation**

Even after fixing the hybrid search regression, "TÜİK aktif toplamı
nedir?" returned the wrong number (-760.049,74 instead of
377.527.395,96). Root cause: OCR/table-flattening produces
"value label value label" ordering (e.g.,
"-760.049,74 AKTİF TOPLAMI 377.527.395,96"), and the model was
matching the number preceding the label instead of following it.

**Fix:** 

Added explicit prompt rules instructing the model to match
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

- ✅ Passed — prompt refinement, combined with the hybrid search fix,
resolved all previously failing queries above.

---

## TC-023 – Expanded Automated Evaluation

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
| Overall Accuracy | 62.50% |
| Answer Accuracy | 62.50% |
| Source Hit@K | 96.43% |
| Errors | 0 |

### Observations

- Retrieval performance remained strong, with a **96.43% Source Hit@K**.
- Most failed cases occurred on dense OCR invoice tables where the correct 
document was retrieved but the LLM returned the fallback response instead of 
extracting the requested value.
- Hallucination handling worked as intended: questions whose answers were not 
present in the indexed documents consistently returned the language-aware 
fallback response instead of fabricated information.

### Analysis

The evaluation highlights a clear distinction between retrieval quality
and answer generation quality.

Retrieval performed consistently, achieving **96.43% Source Hit@K**,
indicating that the hybrid retrieval pipeline usually selected the
correct source document.

Most failures occurred during answer generation rather than retrieval.

The main failure patterns were:

- OCR extraction limitations in complex invoice layouts.
- Failure to extract specific fields despite correct document retrieval.
- Strict answer validation for semantically correct but differently worded 
responses (for example, expected keywords not appearing verbatim).
- Generation failures on dense tabular OCR content despite successful retrieval.

The benchmark also confirmed that multilingual fallback handling works
correctly. All deliberate "not found" questions returned the
language-appropriate fallback response without hallucinating answers.

### Conclusion

The evaluation demonstrates that the hybrid retrieval pipeline is highly
reliable for document selection, while the remaining weaknesses are
primarily related to OCR quality and LLM answer generation on complex
structured documents rather than retrieval itself.

---

### TC-024 – Incremental Document Indexing and Removal

**Description**

Verified that newly uploaded documents are indexed incrementally
without rebuilding the entire index, and that removing a document
correctly updates the retrieval index so deleted content is no longer
returned.

**Procedure**

1. Upload Document A and verify it can be queried.
2. Upload Document B and verify both documents are retrievable.
3. Remove Document A.
4. Verify that queries related to Document A return "not found".
5. Verify that queries related to Document B still return correct answers.

**Status**

- ✅ Passed

---

### TC-025 – FastAPI Web Interface

**Description**

Verified that the FastAPI web interface supports the complete
document-question answering workflow, including document upload,
indexing, retrieval, and answer generation.

**Procedure**

1. Launch the FastAPI application.
2. Open the web interface in a browser.
3. Upload one or more supported documents.
4. Wait for indexing to complete.
5. Submit multiple questions through the interface.
6. Verify that answers are returned successfully.
7. Verify that the retrieved source documents are displayed correctly.

**Status**

- ✅ Passed

---

### TC-026 – Language-Aware Fallback Responses

**Description**

Verified that when the requested information is not present in the
indexed documents, the assistant returns a fallback response in the
same language as the user's query.

**Procedure**

| Query | Expected |
|--------|----------|
| Turkish question with no matching information | Turkish fallback message |
| English question with no matching information | English fallback message |

**Status**

- ✅ Passed

**Observation**

The fallback response language is determined through automatic language
detection and post-generation normalization. As a result, the response
language consistently matches the user's query, regardless of the
language of the indexed documents or retrieved context.

---

### TC-027 – Retrieval Debug Information

**Description**

Verified that retrieval debug information (retrieved chunks, source
documents, and retrieval scores) is available during development for
retrieval analysis and troubleshooting.

**Observation**

The original Streamlit interface displayed detailed retrieval
diagnostics, including retrieved chunks and hybrid retrieval scores.
After migrating to the FastAPI web interface, these diagnostics were
removed from the user interface because they are intended for
development rather than end-user usage. The same information remains
available through `search.py` and the command-line execution of `rag.py`
 for debugging and evaluation.

**Status**

- ✅ Passed

---

## TC-028 – Question During Indexing

**Description**

Verified that the application prevents users from submitting questions
while document indexing is in progress.

**Procedure**

1. Upload one or more documents for indexing.
2. Attempt to submit a question before indexing completes.
3. Observe the chat interface.

**Expected**

The chat input is disabled until indexing completes.

**Status**

- ✅ Passed

**Observation**

This prevents users from receiving incomplete or inconsistent answers
while the document index is still being built, ensuring that retrieval
is performed only after all indexed documents are available.
---

### TC-029 – OCR Resource Cleanup and Word Reconstruction

**Description**

Verified that explicit OCR resource cleanup and the updated word-gap
threshold improve OCR robustness without affecting extraction accuracy.

**Procedure**

1. Process multiple scanned PDF documents.
2. Compare OCR output before and after the changes.
3. Verify words are separated correctly.
4. Confirm no OCR exceptions occur during processing.

**Status**

- ✅ Passed

**Observation**

Explicit resource cleanup improved the stability of the OCR pipeline
without changing the extracted content. Reducing the word-gap threshold
produced more accurate word reconstruction and spacing while introducing
no observable regressions in the tested documents.

---

### TC-030 – Chunking Strategy Evaluation

**Description**

Compared fixed-size and recursive chunking strategies to evaluate their
impact on RAG answer accuracy, source retrieval accuracy, and response
time.

**Procedure**

1. Run the same 32-question evaluation set using fixed chunking with a
   chunk size of 900 and an overlap of 150.
2. Run the same evaluation using recursive chunking with the same chunk
   size and overlap.
3. Compare answer accuracy, source retrieval accuracy, and average
   response time.
4. Review failed questions to identify remaining limitations.

**Results**

| Strategy            | Answer Accuracy | Source Accuracy | Avg. Response Time |
| ------------------- | --------------: | --------------: | -----------------: |
| Fixed (900/150)     |           62.5% |            100% |            8.759 s |
| Recursive (900/150) |           75.0% |          96.43% |            8.681 s |

**Status**

- ✅ Passed

**Observation**

Recursive chunking improved answer accuracy from 62.5% to 75.0% while
maintaining nearly the same average response time.

The results suggest that preserving document structure during chunking
provides more useful context for answer generation than fixed-size
splitting. Source retrieval accuracy decreased slightly from 100% to
96.43%, but the improvement in answer accuracy was more significant.

Based on these results, recursive chunking was selected as the current
default strategy.

Remaining failures were concentrated primarily in OCR-heavy,
table-based, and numeric extraction questions.

---


## Summary of RAG/QA Limitations

Testing across financial tables and a scanned invoice surfaced three
distinct failure modes, in increasing order of severity:

1. **False negatives** Relevant information is successfully retrieved,
but the language model incorrectly responds that the information is
unavailable.
2. **OCR extraction gaps** Dense, multi-section tables are not fully
captured during OCR, making some information unavailable before the
retrieval stage.
3. **Numeric reasoning limitations** Questions involving numerical
values extracted from complex tables remain more error-prone than
descriptive or narrative questions.

These findings indicate that while the system performs reliably for
general document question answering and multilingual retrieval, it is
not yet suitable for production financial or invoice-processing
workloads without additional OCR and table-processing improvements
(see DEVLOG.md for the corresponding design decisions).

Remaining limitations are primarily related to:

- OCR quality on dense tables
- Answer generation over OCR-degraded content
- Numeric extraction from complex layouts

These limitations are documented throughout this report and provide a
clear roadmap for future improvements.

---

## Overall Conclusion

Testing confirmed that the application successfully supports:

- Digital PDF processing
- OCR-based document extraction
- Hybrid retrieval (FAISS + BM25)
- Local RAG generation with Ollama
- FastAPI web interface
- Multiple document uploads
- Turkish and English question answering

The evaluation demonstrates that the retrieval pipeline performs
reliably across multilingual documents and general question answering.
The remaining limitations are primarily associated with OCR quality,
dense tabular document layouts, and numeric question answering rather
than the hybrid retrieval architecture itself.

Overall, the project provides a solid foundation for a local,
privacy-focused document question answering system, with future work
focused on improving OCR accuracy and handling complex financial and
tabular documents.