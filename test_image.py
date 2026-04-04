# Save as test_image.py
import base64, requests, json

with open("sample3.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    "fileName": "sample3.jpg",
    "fileType": "image",
    "fileBase64": b64
}

resp = requests.post(
    "http://localhost:8000/api/document-analyze",
    json=payload,
    headers={
        "Content-Type": "application/json",
        "x-api-key": "sk_docmind_2026_secure"
    }
)
print(json.dumps(resp.json(), indent=2))