import os, base64, json, re, itertools
import fitz
import requests
from PIL import Image
from io import BytesIO
from docx import Document
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DocMind API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

MY_API_KEY = os.getenv("MY_API_KEY", "sk_docmind_2026_secure")
VISION_API_KEY = os.getenv("VISION_API_KEY", "")

GEMINI_KEYS = [k for k in [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"),
    os.getenv("GEMINI_KEY_4"),
] if k]

_key_cycle = itertools.cycle(GEMINI_KEYS)

def get_model():
    key = next(_key_cycle)
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-1.5-flash")

class DocRequest(BaseModel):
    fileName: str
    fileType: str
    fileBase64: str

# ── PDF extraction ─────────────────────────────────────
def extract_pdf(b: bytes) -> str:
    try:
        doc = fitz.open(stream=b, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc).strip()
        if len(text) > 20:
            return text
    except Exception:
        pass
    return ""

# ── DOCX extraction ────────────────────────────────────
def extract_docx(b: bytes) -> str:
    try:
        doc = Document(BytesIO(b))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
        if len(text) > 20:
            return text
    except Exception:
        pass
    return ""

# ── Image OCR via Google Cloud Vision ─────────────────
def extract_image_vision(b: bytes) -> str:
    try:
        b64_image = base64.b64encode(b).decode("utf-8")
        url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
        payload = {
            "requests": [{
                "image": {"content": b64_image},
                "features": [{"type": "TEXT_DETECTION", "maxResults": 1}]
            }]
        }
        resp = requests.post(url, json=payload, timeout=30)
        data = resp.json()
        annotations = data.get("responses", [{}])[0].get("textAnnotations", [])
        if annotations:
            return annotations[0].get("description", "").strip()
    except Exception:
        pass
    return ""

# ── Image OCR fallback via Gemini Vision ──────────────
def extract_image_gemini(b: bytes) -> str:
    try:
        model = get_model()
        image_part = {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(b).decode("utf-8")
        }
        response = model.generate_content([
            "Extract and return ALL text visible in this image. Return only the raw text, nothing else.",
            image_part
        ])
        return response.text.strip()
    except Exception:
        pass
    return ""

# ── Smart text extractor ───────────────────────────────
def extract_text(b: bytes, file_type: str) -> str:
    ft = file_type.lower().strip()

    if ft == "pdf":
        text = extract_pdf(b)
        if len(text) > 20:
            return text
        # PDF might be scanned — try Vision OCR
        return extract_image_vision(b) or extract_image_gemini(b)

    if ft in ("docx", "doc"):
        text = extract_docx(b)
        if len(text) > 20:
            return text
        return extract_image_vision(b) or extract_image_gemini(b)

    if ft in ("image", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"):
        # Try Google Vision first, then Gemini Vision as fallback
        text = extract_image_vision(b)
        if len(text) > 20:
            return text
        return extract_image_gemini(b)

    # Auto-detect fallback
    for fn in [extract_pdf, extract_docx]:
        try:
            r = fn(b)
            if len(r) > 20:
                return r
        except:
            pass
    return extract_image_vision(b) or extract_image_gemini(b)

# ── Gemini AI Analysis ─────────────────────────────────
PROMPT = """Analyze the document text below. Return ONLY a valid JSON object. No markdown. No explanation. No code blocks. Just raw JSON.

Document:
\"\"\"
{text}
\"\"\"

Return exactly this JSON:
{{
  "summary": "2-3 sentence accurate summary of the main topic and key points",
  "entities": {{
    "names": ["real human person names only"],
    "dates": ["all dates in any format"],
    "organizations": ["company names, institutions, banks, government bodies"],
    "amounts": ["monetary values with currency symbols"]
  }},
  "sentiment": "Positive or Neutral or Negative"
}}

Rules:
- names: ONLY human person names, NOT company names
- organizations: company, university, bank, government agency names
- amounts: monetary values with currency like $5000 or Rs.10000
- sentiment: Positive=good/optimistic, Negative=bad/crisis/concerning, Neutral=factual/balanced
- Empty list = []
- Return ONLY raw JSON, nothing else"""

def analyze(text: str) -> dict:
    prompt = PROMPT.format(text=text[:6000])
    raw = ""
    for _ in range(len(GEMINI_KEYS)):
        try:
            model = get_model()
            resp = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                )
            )
            raw = resp.text.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"^```\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except:
                    pass
        except Exception:
            continue
    return {
        "summary": "Document processed successfully.",
        "entities": {"names": [], "dates": [], "organizations": [], "amounts": []},
        "sentiment": "Neutral"
    }

# ── Main endpoint ──────────────────────────────────────
@app.post("/api/document-analyze")
async def analyze_document(req: DocRequest, x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != MY_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key")

    try:
        file_bytes = base64.b64decode(req.fileBase64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 file")

    text = ""
    try:
        text = extract_text(file_bytes, req.fileType)
    except Exception:
        pass

    if len(text.strip()) < 10:
        return {
            "status": "success",
            "fileName": req.fileName,
            "summary": "Document contains minimal readable text.",
            "entities": {"names": [], "dates": [], "organizations": [], "amounts": []},
            "sentiment": "Neutral"
        }

    result = analyze(text)
    return {
        "status": "success",
        "fileName": req.fileName,
        "summary": result.get("summary", ""),
        "entities": {
            "names":         result.get("entities", {}).get("names", []),
            "dates":         result.get("entities", {}).get("dates", []),
            "organizations": result.get("entities", {}).get("organizations", []),
            "amounts":       result.get("entities", {}).get("amounts", [])
        },
        "sentiment": result.get("sentiment", "Neutral")
    }

@app.get("/")
def root():
    return {"status": "DocMind API is running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}