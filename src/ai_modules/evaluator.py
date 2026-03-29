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
                "model": "deepseek-r1:7b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 1
                }
            }
        )

        return response.json()["response"]

    except Exception as e:
        return f"Error: {e}"