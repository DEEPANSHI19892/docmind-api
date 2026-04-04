import os, base64, json, re, itertools
import fitz
import requests
from PIL import Image
from io import BytesIO
from docx import Document
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DocMind API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MY_API_KEY = os.getenv("MY_API_KEY", "sk_docmind_2026_secure")
VISION_API_KEY = os.getenv("VISION_API_KEY", "")

GEMINI_KEYS = [k for k in [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"),
    os.getenv("GEMINI_KEY_4"),
] if k]

_cycle = itertools.cycle(GEMINI_KEYS)

def next_client():
    return genai.Client(api_key=next(_cycle))

class DocRequest(BaseModel):
    fileName: str
    fileType: str
    fileBase64: str

def extract_pdf(b):
    try:
        doc = fitz.open(stream=b, filetype="pdf")
        t = "\n".join(p.get_text() for p in doc).strip()
        if len(t) > 20: return t
    except: pass
    return ""

def extract_docx(b):
    try:
        doc = Document(BytesIO(b))
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip(): parts.append(cell.text.strip())
        t = "\n".join(parts).strip()
        if len(t) > 20: return t
    except: pass
    return ""

def extract_image_vision(b):
    if not VISION_API_KEY: return ""
    try:
        img = Image.open(BytesIO(b))
        if img.mode != "RGB": img = img.convert("RGB")
        if max(img.size) > 2000: img.thumbnail((2000,2000), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
        r = requests.post(url, json={"requests":[{"image":{"content":b64},"features":[{"type":"TEXT_DETECTION","maxResults":1}]}]}, timeout=30)
        ann = r.json().get("responses",[{}])[0].get("textAnnotations",[])
        if ann: return ann[0].get("description","").strip()
    except: pass
    return ""

def extract_image_gemini(b):
    try:
        img = Image.open(BytesIO(b))
        if img.mode != "RGB": img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        client = next_client()
        r = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role":"user","parts":[
                {"text":"Extract ALL text from this image. Return only the raw text."},
                {"inline_data":{"mime_type":"image/jpeg","data":b64}}
            ]}]
        )
        return r.text.strip()
    except: pass
    return ""

def extract_text(b, file_type):
    ft = file_type.lower().strip()
    if ft == "pdf":
        t = extract_pdf(b)
        if len(t) > 20: return t
        try:
            doc = fitz.open(stream=b, filetype="pdf")
            parts = []
            for page in doc:
                pix = page.get_pixmap(dpi=150)
                img_b = pix.tobytes("jpeg")
                t2 = extract_image_vision(img_b) or extract_image_gemini(img_b)
                if t2: parts.append(t2)
            if parts: return "\n".join(parts)
        except: pass
        return ""
    if ft in ("docx","doc"):
        t = extract_docx(b)
        if len(t) > 20: return t
        return extract_image_vision(b) or extract_image_gemini(b)
    if ft in ("image","jpg","jpeg","png","gif","bmp","tiff","webp"):
        t = extract_image_vision(b)
        if len(t) > 20: return t
        return extract_image_gemini(b)
    for fn in [extract_pdf, extract_docx]:
        try:
            r = fn(b)
            if len(r) > 20: return r
        except: pass
    return extract_image_vision(b) or extract_image_gemini(b)

PROMPT = """Analyze the document text. Return ONLY raw JSON, no markdown, no explanation.

Document:
\"\"\"{text}\"\"\"

Return this exact JSON:
{{
  "summary": "2-3 sentence accurate summary of the main topic and key points",
  "entities": {{
    "names": ["human person names only"],
    "dates": ["all dates in any format"],
    "organizations": ["company, institution, university, government body names"],
    "amounts": ["monetary values with currency symbols"]
  }},
  "sentiment": "Positive or Neutral or Negative"
}}

Rules:
- names: ONLY human person names, NOT company names
- sentiment: Positive=good news/growth, Negative=crisis/loss/breach, Neutral=factual/balanced
- Empty list = []
- Return ONLY the JSON"""

def analyze(text):
    prompt = PROMPT.format(text=text[:6000])
    raw = ""
    for _ in range(len(GEMINI_KEYS) + 2):
        try:
            client = next_client()
            r = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            raw = r.text.strip()
            raw = re.sub(r"^```json\s*","",raw,flags=re.MULTILINE)
            raw = re.sub(r"^```\s*","",raw,flags=re.MULTILINE)
            raw = re.sub(r"\s*```$","",raw,flags=re.MULTILINE)
            raw = raw.strip()
            result = json.loads(raw)
            if "summary" in result and "entities" in result and "sentiment" in result:
                return result
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    result = json.loads(m.group())
                    if "summary" in result: return result
                except: pass
        except: continue
    return {"summary":"Document processed.","entities":{"names":[],"dates":[],"organizations":[],"amounts":[]},"sentiment":"Neutral"}

@app.post("/api/document-analyze")
async def analyze_document(req: DocRequest, x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != MY_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        file_bytes = base64.b64decode(req.fileBase64)
    except:
        raise HTTPException(status_code=400, detail="Invalid base64")

    text = ""
    try: text = extract_text(file_bytes, req.fileType)
    except: pass

    if not text or len(text.strip()) < 5:
        try:
            d = file_bytes.decode("utf-8", errors="ignore").strip()
            if len(d) > 20: text = d
        except: pass

    if not text or len(text.strip()) < 5:
        return {"status":"success","fileName":req.fileName,
                "summary":"Document received but contains no extractable text.",
                "entities":{"names":[],"dates":[],"organizations":[],"amounts":[]},
                "sentiment":"Neutral"}

    result = analyze(text)
    return {
        "status": "success",
        "fileName": req.fileName,
        "summary": result.get("summary",""),
        "entities": {
            "names": result.get("entities",{}).get("names",[]),
            "dates": result.get("entities",{}).get("dates",[]),
            "organizations": result.get("entities",{}).get("organizations",[]),
            "amounts": result.get("entities",{}).get("amounts",[])
        },
        "sentiment": result.get("sentiment","Neutral")
    }

@app.get("/")
def root(): return {"status":"DocMind API is running","version":"1.0.0"}

@app.get("/health")
@app.head("/health")
def health(): return {"status":"healthy"}