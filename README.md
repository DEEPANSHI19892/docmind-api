DocMind — AI-Powered Document Analysis & Extraction API

📌 Description

DocMind is a production-ready document intelligence API that extracts, analyzes, and structures information from:

📄 PDFs (text & scanned)
📝 DOCX files
🖼 Images (JPG, PNG, TIFF, BMP)

It is engineered for automated evaluation environments with strict JSON compliance, low latency, and high reliability.

🧠 AI Tools Used

🔹 Google Gemini 2.0 Flash
2–3 sentence structured summary
Entity extraction (names, dates, organizations, amounts)
Sentiment classification (Positive / Neutral / Negative)
Strict JSON output enforcement

🔹 Google Cloud Vision API
OCR for images
OCR for scanned PDFs

🔹 Groq (Fallback LLM)
Backup analysis if Gemini fails
Ensures stability during automation testing

🔹 Claude (Anthropic)
Architecture & development assistance

🔹 ChatGPT
Optimization, debugging guidance, and documentation refinement

🏗 Tech Stack

Python 3.11
FastAPI
PyMuPDF (fitz) – PDF extraction
python-docx – DOCX extraction
Google Cloud Vision API – OCR
Gemini 2.0 Flash (google-genai) – Primary LLM
Groq – Fallback LLM
Render.com – Deployment

🌐 API Specification

Endpoint
POST /api/document-analyze

Headers
Content-Type: application/json
x-api-key: YOUR_API_KEY

Request Body
{
  "fileName": "document.pdf",
  "fileType": "pdf",
  "fileBase64": "base64_encoded_file_content"
}
Supported fileType
pdf
docx
image
Success Response
{
  "status": "success",
  "fileName": "document.pdf",
  "summary": "Concise 2–3 sentence summary.",
  "entities": {
    "names": [],
    "dates": [],
    "organizations": [],
    "amounts": []
  },
  "sentiment": "Neutral"
}

⚙️ Architecture Overview

1️⃣ Extraction Layer

Text-based PDF → PyMuPDF
Scanned PDF → Page images → Vision OCR
DOCX → Paragraph + table extraction
Images → Vision OCR

2️⃣ AI Analysis Layer

Structured prompt → Gemini 2.0 Flash
Strict JSON output required
Regex-based JSON recovery if malformed

3️⃣ Reliability Layer

4-key Gemini rotation (itertools.cycle)
Automatic retry on quota errors
Groq fallback model
Guaranteed structured response

⚡ Performance Design

In-memory processing (no disk writes)
OCR only when required
Optimized prompt size
Multi-key rotation prevents rate-limit delays
Target response time: <7 seconds

🧪 Setup

git clone https://github.com/YOUR_USERNAME/docmind-api
cd docmind-api
python -m venv venv
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

🔐 Environment Variables
MY_API_KEY=
VISION_API_KEY=
GEMINI_KEY_1=
GEMINI_KEY_2=
GEMINI_KEY_3=
GEMINI_KEY_4=
GROQ_KEY=

🩺 Health Check
GET /health

Response:

{
  "status": "healthy"
}

🏆 Competitive Strengths

✔ Handles scanned + text PDFs
✔ Vision OCR integration
✔ Multi-LLM fallback
✔ 4-key rotation for rate-limit protection
✔ Strict JSON compliance
✔ Automation-test optimized
✔ Production deployment

🎯 Conclusion

DocMind is a resilient, AI-powered document intelligence API designed for structured extraction, fast response, and reliable automated evaluation performance.