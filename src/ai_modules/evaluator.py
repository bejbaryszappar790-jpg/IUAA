import requests
import re
from src.ai_modules.prompts import build_full_prompt
from src.ai_modules.cert_val import verify_certificate
 
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "MFDoom/deepseek-r1-tool-calling:8b"

def truncate_text(text: str, max_chars: int = 3000) -> str:
    return text[:max_chars]

def extract_scores(ai_text: str) -> dict:
    """
    Извлекает баллы из текстового ответа ИИ.
    Если ИИ не указал баллы, возвращает базовые значения 6 (чуть выше среднего).
    """
    scores = {"leadership": 6, "growth": 6, "authenticity": 6}
    
    # Ищем паттерны: "Лидерство: 8/10" или "Лидерство: 8"
    patterns = {
        "leadership": r"Лидерство:\s*(\d+)",
        "growth": r"Рост:\s*(\d+)",
        "authenticity": r"Подлинность:\s*(\d+)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, ai_text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            # Ограничиваем диапазон от 0 до 10
            scores[key] = max(0, min(10, val))
            
    return scores
 
def evaluate_candidate(
    text: str,
    cert_file: str = None,
    test_date: str = None,
    cert_type: str = None
) -> tuple: # Возвращает (content, scores_dict)
 
    # Шаг 1: Подготовка текста
    # Если это изображение (Баг №3), мы помечаем это для промпта
    is_image_only = "Image file detected" in text
    clean_text = truncate_text(text)
 
    # Шаг 2: Проверка сертификата техническими модулями
    cert_result = None
    if cert_file and test_date and cert_type:
        try:
            cert_result = verify_certificate(cert_file, test_date, cert_type)
        except Exception as e:
            print(f"[evaluator] Ошибка технической проверки: {e}")
 
    # Шаг 3: Сборка промпта
    prompt = build_full_prompt(essay_text=clean_text, cert_result=cert_result)
 
    # Шаг 4: Запрос к Ollama
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.2, "top_p": 0.9}
            },
            timeout=120
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        
        # Шаг 5: Извлечение баллов (Решение Бага №1)
        scores = extract_scores(content)
        
        return content, scores
 
    except Exception as e:
        error_msg = f"Ошибка анализа ИИ: {str(e)}"
        print(f"[evaluator] {error_msg}")
        return error_msg, {"leadership": 5, "growth": 5, "authenticity": 5}