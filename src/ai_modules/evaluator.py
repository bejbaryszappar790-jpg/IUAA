import requests
from .prompts import SYSTEM_PROMPT
from .cert_val import verify_certificate

OLLAMA_URL = "http://localhost:11434/api/chat"

def truncate_text(text, max_chars=3000):
    return text[:max_chars]

def format_cert(cert):
    if not cert:
        return "CERTIFICATE: NOT PROVIDED"

    expiry = cert.get("expiry", {})
    return f"""
CERTIFICATE VERIFICATION:
- QR found: {cert.get("qr_found")}
- QR URL: {cert.get("qr_url")}
- Link valid: {cert.get("link_valid")}
- Link message: {cert.get("link_message")}
- Expired: {expiry.get("is_expired")}
- Days left: {expiry.get("days_left")}
"""

def evaluate_candidate(text, cert_file=None, test_date=None, cert_type=None):
    text = truncate_text(text)

    cert_result = None

    # Run cert validation BEFORE LLM
    if cert_file and test_date and cert_type:
        cert_result = verify_certificate(cert_file, test_date, cert_type)

    prompt = f"""
{SYSTEM_PROMPT}

{format_cert(cert_result)}

CANDIDATE ESSAY:
{text}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "MFDoom/deepseek-r1-tool-calling:8b",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }
        )

        return response.json()["message"]["content"]

    except Exception as e:
        return f"Error: {e}"