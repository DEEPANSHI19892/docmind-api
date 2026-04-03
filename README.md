# DocMind — AI-Powered Document Analysis API

## Description
Intelligent document processing API that extracts, analyses, and summarises
content from PDF, DOCX, and image files using OCR and Google Gemini AI.

## Tech Stack
- Python 3.11 + FastAPI
- PyMuPDF — PDF extraction
- python-docx — DOCX extraction
- pytesseract + Pillow — OCR for images
- Google Gemini 1.5 Flash — AI analysis
- Render — Deployment

## AI Tools Used
- Google Gemini 1.5 Flash — summarisation, entity extraction, sentiment analysis
- Claude (Anthropic) — development assistance

## Setup Instructions
1. git clone https://github.com/DEEPANSHI19892/docmind-api
2. pip install -r requirements.txt
3. Install Tesseract OCR
4. Copy .env.example to .env and fill real keys
5. uvicorn main:app --host 0.0.0.0 --port 8000

## API Usage
POST /api/document-analyze
Header: x-api-key: YOUR_KEY
Body: { "fileName": "file.pdf", "fileType": "pdf", "fileBase64": "base64string" }

## Approach
- PDF: PyMuPDF extracts full text with layout preservation
- DOCX: python-docx reads all paragraph content  
- Images: pytesseract performs OCR to extract text
- Gemini 1.5 Flash generates summary, entities, sentiment
- 4-key rotation ensures zero rate limiting