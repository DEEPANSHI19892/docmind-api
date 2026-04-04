# DocMind — AI-Powered Document Analysis & Extraction API

## Description
DocMind is an intelligent document processing API that extracts, analyses, and summarises content from PDF, DOCX, and image files. It leverages Google Gemini AI and Google Cloud Vision OCR to understand document structure and extract key information automatically.

## Tech Stack
- **Language/Framework:** Python 3.11 + FastAPI
- **PDF Extraction:** PyMuPDF (fitz)
- **DOCX Extraction:** python-docx
- **OCR for Images:** Google Cloud Vision API
- **AI Model:** Google Gemini 2.0 Flash (google-genai)
- **Deployment:** Render.com

## AI Tools Used
- Google Gemini 2.0 Flash — summarisation, entity extraction, sentiment analysis
- Google Cloud Vision API — OCR text extraction from images and scanned PDFs
- Claude (Anthropic) — development assistance

## API Usage

### Endpoint
POST /api/document-analyze

### Headers
Content-Type: application/json
x-api-key: YOUR_API_KEY

### Request Body
```json
{
  "fileName": "document.pdf",
  "fileType": "pdf",
  "fileBase64": "base64_encoded_file_content"
}
```

### Supported fileType values
- `pdf` — PDF documents
- `docx` — Word documents
- `image` — JPG, PNG, BMP, TIFF images

### Response
```json
{
  "status": "success",
  "fileName": "document.pdf",
  "summary": "2-3 sentence summary of document content",
  "entities": {
    "names": ["person names"],
    "dates": ["dates found"],
    "organizations": ["company and institution names"],
    "amounts": ["monetary values"]
  },
  "sentiment": "Positive or Neutral or Negative"
}
```

## Setup Instructions
1. `git clone https://github.com/YOUR_USERNAME/docmind-api`
2. `cd docmind-api`
3. `python -m venv venv && venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in API keys
6. `uvicorn main:app --host 0.0.0.0 --port 8000`

## Architecture Overview
- FastAPI receives Base64 encoded document
- PyMuPDF extracts text from PDFs (text-based)
- Scanned PDFs: converted to images via PyMuPDF, then OCR via Google Vision
- DOCX: python-docx extracts all paragraphs and tables
- Images: Google Cloud Vision API for OCR, Gemini Vision as fallback
- Extracted text sent to Gemini 2.0 Flash for summary, entities, sentiment
- 4-key rotation prevents rate limiting

## Approach
- **PDF:** PyMuPDF first. If text < 20 chars (scanned), convert pages to JPEG and run OCR.
- **DOCX:** python-docx reads paragraphs and table cells.
- **Images:** Google Cloud Vision API primary, Gemini Vision fallback.
- **AI Analysis:** Gemini 2.0 Flash with structured JSON prompt, regex fallback for JSON parsing.
- **Key rotation:** 4 Gemini API keys cycled to handle rate limits across 15 test cases.

## Known Limitations
- Very large files (>50MB) may timeout on free hosting tier
- Handwritten text OCR accuracy depends on image quality

## Environment Variables
See `.env.example` for required variables.