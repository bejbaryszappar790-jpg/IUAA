import requests
import re
from src.ai_modules.prompts import build_full_prompt
from src.ai_modules.cert_val import verify_certificate
 
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "MFDoom/deepseek-r1-tool-calling:8b"
 
 
def hard_parse_facts(text: str) -> str:
    """Программный поиск фактов в тексте — подсказки для LLM"""
    facts = []
    t = text.lower()
 
    if any(x in t for x in ["ниш", "nis", "назарбаев", "рфмш", "rfmsh", "бил", "bil"]):
        facts.append("!!! ВНИМАНИЕ: Кандидат из ЭЛИТНОЙ школы (НИШ/РФМШ/БИЛ). Уровень сложности обучения очень высокий.")
 
    sat_match = re.search(r"sat.*?(1[0-9]{3})", t)
    if sat_match:
        facts.append(f"!!! ФАКТ: Обнаружен результат SAT {sat_match.group(1)}.")
 
    if "ucmas" in t:
        facts.append("!!! ФАКТ: Сертификат UCMAS (ментальная арифметика).")
 
    return "\n".join(facts)
 
 
def extract_scores(ai_text: str) -> dict:
    """Извлекает числовые баллы из ответа LLM"""
    scores = {"leadership": 5, "growth": 5, "authenticity": 5}
    patterns = {
        "leadership":   r"Лидерство:\s*(\d+)",
        "growth":       r"Рост:\s*(\d+)",
        "authenticity": r"Подлинность:\s*(\d+)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, ai_text, re.IGNORECASE)
        if match:
            scores[key] = max(0, min(10, int(match.group(1))))
    return scores
 
 
def evaluate_candidate(
    text: str,
    cert_file: str = None,
    test_date: str = None,
    cert_type: str = None
) -> tuple[str, dict]:
    """
    Главная функция оценки.
    Возвращает: (текст_отчёта, словарь_баллов)
    Пример: ("Лидерство: 7/10...", {"leadership": 7, "growth": 6, "authenticity": 5})
    """
    # Шаг 1: Извлекаем жёсткие факты из текста
    extra_facts = hard_parse_facts(text)
    full_content = f"{extra_facts}\n\n{text[:4000]}" if extra_facts else text[:4000]
 
    # Шаг 2: Проверка сертификата
    cert_result = None
    if cert_file and test_date:
        try:
            cert_result = verify_certificate(cert_file, test_date, cert_type or "IELTS")
        except Exception as e:
            print(f"[cert_val] Ошибка: {e}")
 
    # Шаг 3: Собираем промпт
    prompt = build_full_prompt(full_content, cert_result)
 
    # Шаг 4: Запрос к Ollama
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9}
            },
            timeout=120
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        scores = extract_scores(content)
        return content, scores
 
    except requests.exceptions.Timeout:
        msg = "Ошибка: модель не ответила за 2 минуты. Попробуйте снова."
        return msg, {"leadership": 5, "growth": 5, "authenticity": 5}
    except requests.exceptions.ConnectionError:
        msg = "Ошибка: Ollama не запущена. Выполните 'ollama serve' в терминале."
        return msg, {"leadership": 5, "growth": 5, "authenticity": 5}
    except Exception as e:
        msg = f"Ошибка анализа: {str(e)}"
        return msg, {"leadership": 5, "growth": 5, "authenticity": 5}
 