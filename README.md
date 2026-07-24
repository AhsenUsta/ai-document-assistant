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

## Current Stage

The project currently implements the document loading and preprocessing pipeline, including:

- PDF text extraction
- OCR for scanned documents
- Image OCR
- Text chunking

Place your own PDF, PNG or JPG files inside the `data/` folder.

Run the pipeline:

```bash
python loaddocs.py
```