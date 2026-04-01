import requests
from .prompts import SYSTEM_PROMPT

OLLAMA_URL = "http://localhost:11434/api/generate"

def truncate_text(text, max_chars=3000):
    return text[:max_chars]

def evaluate_candidate(text):
    text = truncate_text(text)

    prompt = SYSTEM_PROMPT + f"\n\n{text}"

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "MFDoom/deepseek-r1-tool-calling:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }
        )

        return response.json()["response"]

    except Exception as e:
        return f"Error: {e}"