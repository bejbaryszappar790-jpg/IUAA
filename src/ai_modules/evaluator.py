import requests
from src.ai_modules.prompts import build_full_prompt
from src.ai_modules.cert_val import verify_certificate
 
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "MFDoom/deepseek-r1-tool-calling:8b"
 
def truncate_text(text: str, max_chars: int = 3000) -> str:
    return text[:max_chars]
 
def evaluate_candidate(
    text: str,
    cert_file: str = None,
    test_date: str = None,
    cert_type: str = None
) -> str:
 
    # Шаг 1: обрезаем текст
    text = truncate_text(text)
 
    # Шаг 2: проверка сертификата ПЕРЕД LLM
    cert_result = None
    if cert_file and test_date and cert_type:
        try:
            cert_result = verify_certificate(cert_file, test_date, cert_type)
        except Exception as e:
            print(f"[cert_val] Ошибка проверки сертификата: {e}")
            cert_result = None
 
    # Шаг 3: собираем промпт через build_full_prompt
    prompt = build_full_prompt(essay_text=text, cert_result=cert_result)
 
    # Шаг 4: отправляем в Ollama
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
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
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
 
    except requests.exceptions.Timeout:
        return "Ошибка: модель не ответила за 2 минуты. Попробуйте ещё раз."
    except requests.exceptions.ConnectionError:
        return "Ошибка: Ollama не запущена. Выполните 'ollama serve' в терминале."
    except KeyError:
        return f"Ошибка: неожиданный формат ответа от Ollama. Ответ: {response.text[:300]}"
    except Exception as e:
        return f"Ошибка: {e}"