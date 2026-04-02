"""
web_footprint.py — Модуль проверки браузерного следа кандидата (Исправленная версия)
"""

import requests
import time
import re
from urllib.parse import quote
from duckduckgo_search import DDGS  # Библиотека из requirements.txt

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ═══════════════════════════════════════
# 1. ПОИСК ЧЕРЕЗ DUCKDUCKGO (С РЕЗЕРВОМ)
# ═══════════════════════════════════════

def search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """
    Ищет информацию. Сначала через надежную библиотеку DDGS, 
    затем (если не вышло) через ручной парсинг HTML.
    """
    # МЕТОД А: Используем современную библиотеку (Решение Бага №2)
    try:
        with DDGS() as ddgs:
            results = []
            ddgs_gen = ddgs.text(query, max_results=max_results)
            for r in ddgs_gen:
                results.append({
                    "title": r.get('title', ''),
                    "snippet": r.get('body', ''),
                    "url": r.get('href', '')
                })
            if results:
                print(f"[web_footprint] Успешный поиск через DDGS для: {query[:30]}...")
                return results
    except Exception as e:
        print(f"[web_footprint] Библиотека DDGS временно недоступна, переход на ручной парсинг: {e}")

    # МЕТОД Б: Ручной парсинг (Твой старый код как запасной план)
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        text = response.text
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', text, re.DOTALL)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</div>', text, re.DOTALL)
        urls = re.findall(r'class="result__url"[^>]*>(.*?)</a>', text, re.DOTALL)

        def clean_html(raw):
            return re.sub(r'<[^>]+>', '', raw).strip()

        fallback_results = []
        for i in range(min(max_results, len(titles))):
            fallback_results.append({
                "title": clean_html(titles[i]),
                "snippet": clean_html(snippets[i]) if i < len(snippets) else "",
                "url": clean_html(urls[i]) if i < len(urls) else "",
            })
        return fallback_results
    except Exception as e:
        return [{"error": str(e), "title": "Ошибка поиска", "snippet": "", "url": ""}]

# ═══════════════════════════════════════
# 2. ПРОВЕРКА ОДНОГО ДОСТИЖЕНИЯ
# ═══════════════════════════════════════

def verify_achievement(candidate_name: str, achievement: str, year: str = "") -> dict:
    query = f"{candidate_name} {achievement} {year}".strip()
    
    # Небольшая пауза, чтобы DuckDuckGo нас не забанил
    time.sleep(1) 
    results = search_duckduckgo(query, max_results=5)

    name_parts = candidate_name.lower().split()
    found_with_name = False
    found_event = False
    matching_urls = []

    for r in results:
        if "error" in r or not r.get("title"): continue
        
        combined = (r.get("title", "") + " " + r.get("snippet", "")).lower()
        
        # Проверяем имя (минимум 3 символа в части имени)
        if any(part in combined for part in name_parts if len(part) > 2):
            found_with_name = True
            matching_urls.append(r.get("url", ""))

        # Проверяем ключевые слова из достижения
        ach_words = achievement.lower().split()
        matches = sum(1 for w in ach_words if len(w) > 3 and w in combined)
        if matches >= 2:
            found_event = True

    if found_with_name:
        status, conf, msg = "confirmed", "Высокая", "✅ Найдено прямое подтверждение"
    elif found_event:
        status, conf, msg = "partial", "Средняя", "⚠️ Событие найдено, связь с именем неявная"
    else:
        status, conf, msg = "not_found", "Низкая", "❌ Не найдено в открытых источниках"

    return {
        "achievement": achievement,
        "status": status,
        "confidence": conf,
        "message": msg,
        "links": matching_urls[:2]
    }

# ═══════════════════════════════════════
# 3. ПРОВЕРКА GITHUB
# ═══════════════════════════════════════

def check_github(github_username: str) -> dict:
    if not github_username:
        return {"found": False, "message": "GitHub не указан"}
    
    username = github_username.strip("/").split("/")[-1].replace("@", "")
    try:
        url = f"https://api.github.com/users/{username}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 404:
            return {"found": False, "message": f"Профиль {username} не найден"}
        
        data = res.json()
        repos = data.get("public_repos", 0)
        stars = 0 # Для звезд нужен доп. запрос, для MVP хватит репозиториев
        
        level = "Высокая" if repos > 10 else "Средняя" if repos > 3 else "Низкая"
        
        return {
            "found": True,
            "username": username,
            "repos": repos,
            "activity": level,
            "url": f"https://github.com/{username}",
            "message": f"✅ GitHub: {repos} репо, активность {level}"
        }
    except Exception as e:
        return {"found": False, "message": f"Ошибка GitHub: {str(e)}"}

# ═══════════════════════════════════════
# 4. ОБЩИЙ ВЕРДИКТ
# ═══════════════════════════════════════

def check_web_footprint(candidate_name, achievements=None, github_username=None):
    verified_ach = []
    if achievements:
        for ach in achievements:
            res = verify_achievement(candidate_name, ach.get("title", ""), ach.get("year", ""))
            verified_ach.append(res)

    github_res = check_github(github_username) if github_username else None
    
    # Считаем общий уровень доверия
    confirmed_count = sum(1 for a in verified_ach if a["status"] == "confirmed")
    trust = "Высокий" if confirmed_count > 0 or (github_res and github_res["found"]) else "Низкий"

    return {
        "overall_trust": trust,
        "github": github_res,
        "achievements": verified_ach,
        "summary": f"Доверие: {trust}. Подтверждено достижений: {confirmed_count}"
    }