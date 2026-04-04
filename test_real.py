# Save this as test_real.py in F:\docmind-api\
import base64, requests, json

# Test with the AI article text directly as PDF-type
text = """Technology Industry Analysis: Expansion of Artificial Intelligence Innovation
The global technology sector has experienced significant growth in artificial intelligence
development over the past few years. Google, Microsoft, and NVIDIA have invested heavily.
Academic institutions like Harvard University are establishing AI laboratories.
John Smith from MIT reported revenue of $5 million on 15 March 2026."""

b64 = base64.b64encode(text.encode()).decode()

payload = {
    "fileName": "test.pdf",
    "fileType": "pdf",
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