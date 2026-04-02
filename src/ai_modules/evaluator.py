import re
import requests
from src.ai_modules.prompts import build_full_prompt
from src.ai_modules.cert_val import verify_certificate
 
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "MFDoom/deepseek-r1-tool-calling:8b"
 
 
def extract_scores(ai_text: str) -> dict:
    """Извлекает числовые баллы из ответа LLM"""
    scores = {
        "experience":    5,
        "potential":     5,
        "growth":        5,
        "authenticity":  5,
    }
    patterns = {
        "experience":   r"Опыт:\s*(\d+)",
        "potential":    r"Потенциал:\s*(\d+)",
        "growth":       r"Рост:\s*(\d+)",
        "authenticity": r"Подлинность документов:\s*(\d+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, ai_text, re.IGNORECASE)
        if match:
            scores[key] = max(0, min(10, int(match.group(1))))
    return scores
 
 
def evaluate_candidate(
    candidate_text: str,
    cert_file: str = None,
    test_date: str = None,
    cert_type: str = None,
) -> tuple[str, dict]:
    """
    Оценка кандидата по опыту, потенциалу, росту и подлинности документов.
 
    Параметры:
        candidate_text: описание кандидата (достижения, ЕНТ, мотивация и т.д.)
        cert_file:      путь к файлу сертификата (jpg/png)
        test_date:      дата сдачи теста в формате YYYY-MM-DD
        cert_type:      тип сертификата (IELTS, UCMAS и т.д.)
 
    Возвращает:
        (текст_отчёта, словарь_баллов)
        Пример: ("Опыт: 7/10...", {"experience": 7, "potential": 8, "growth": 6, "authenticity": 9})
    """
    # Шаг 1: Верификация сертификата (если передан)
    cert_result = None
    if cert_file and test_date:
        try:
            cert_result = verify_certificate(cert_file, test_date, cert_type or "IELTS")
        except Exception as e:
            print(f"[cert_val] Ошибка верификации: {e}")
 
    # Шаг 2: Сборка промпта
    prompt = build_full_prompt(candidate_text, cert_result)
 
    # Шаг 3: Запрос к Ollama
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9},
            },
            timeout=120,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        scores = extract_scores(content)
        return content, scores
 
    except requests.exceptions.Timeout:
        msg = "Ошибка: модель не ответила за 2 минуты. Попробуйте снова."
        return msg, {"experience": 5, "potential": 5, "growth": 5, "authenticity": 5}
    except requests.exceptions.ConnectionError:
        msg = "Ошибка: Ollama не запущена. Выполните 'ollama serve' в терминале."
        return msg, {"experience": 5, "potential": 5, "growth": 5, "authenticity": 5}
    except Exception as e:
        msg = f"Ошибка анализа: {str(e)}"
        return msg, {"experience": 5, "potential": 5, "growth": 5, "authenticity": 5}
 