"""
web_footprint.py — Модуль проверки браузерного следа кандидата
 
Логика:
1. Кандидат указывает достижения в резюме
2. ИИ ищет подтверждение в интернете через DuckDuckGo
3. Результат: подтверждено / не найдено / частично найдено
 
Платформы: DuckDuckGo (бесплатно, без API ключа)
"""
 
import requests
import time
from urllib.parse import quote
 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}
 
# ═══════════════════════════════════════
# 1. ПОИСК ЧЕРЕЗ DUCKDUCKGO
# ═══════════════════════════════════════
 
def search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """
    Ищет информацию через DuckDuckGo HTML поиск.
    Возвращает список найденных результатов.
    """
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
 
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
 
        # Простой парсинг без beautifulsoup
        results = []
        text = response.text
 
        # Ищем заголовки результатов
        import re
        # DuckDuckGo возвращает результаты в тегах <a class="result__a">
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', text, re.DOTALL)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</div>', text, re.DOTALL)
        urls = re.findall(r'class="result__url"[^>]*>(.*?)</a>', text, re.DOTALL)
 
        # Чистим HTML теги
        def clean_html(raw):
            return re.sub(r'<[^>]+>', '', raw).strip()
 
        for i in range(min(max_results, len(titles))):
            results.append({
                "title": clean_html(titles[i]) if i < len(titles) else "",
                "snippet": clean_html(snippets[i]) if i < len(snippets) else "",
                "url": clean_html(urls[i]) if i < len(urls) else "",
            })
 
        return results
 
    except requests.exceptions.Timeout:
        return [{"error": "Таймаут поиска", "title": "", "snippet": "", "url": ""}]
    except Exception as e:
        return [{"error": str(e), "title": "", "snippet": "", "url": ""}]
 
 
# ═══════════════════════════════════════
# 2. ПРОВЕРКА ОДНОГО ДОСТИЖЕНИЯ
# ═══════════════════════════════════════
 
def verify_achievement(candidate_name: str, achievement: str, year: str = "") -> dict:
    """
    Проверяет конкретное достижение кандидата в интернете.
 
    Пример:
        candidate_name = "Алибек Дюсенов"
        achievement = "1 место на чемпионате Казахстана по программированию"
        year = "2023"
    """
    # Формируем поисковый запрос
    query = f"{candidate_name} {achievement} {year}".strip()
    query_kz = f"{achievement} {year} Казахстан победитель"  # запрос без имени
 
    time.sleep(1)  # вежливая пауза чтобы не получить бан
    results = search_duckduckgo(query, max_results=5)
 
    # Проверяем упоминается ли имя кандидата в результатах
    name_parts = candidate_name.lower().split()
    found_with_name = False
    found_event = False
    matching_urls = []
 
    for r in results:
        if "error" in r:
            continue
        combined = (r.get("title", "") + " " + r.get("snippet", "")).lower()
 
        # Проверяем упоминание имени
        if any(part in combined for part in name_parts if len(part) > 2):
            found_with_name = True
            matching_urls.append(r.get("url", ""))
 
        # Проверяем упоминание события
        achievement_words = achievement.lower().split()
        if sum(1 for w in achievement_words if w in combined) >= 2:
            found_event = True
 
    # Определяем статус
    if found_with_name:
        status = "confirmed"
        confidence = "Высокая"
        message = f"✅ Найдено подтверждение с упоминанием имени кандидата"
    elif found_event:
        status = "partial"
        confidence = "Средняя"
        message = f"⚠️ Событие найдено, но имя кандидата не упоминается"
    else:
        status = "not_found"
        confidence = "Низкая"
        message = f"❌ Подтверждение не найдено в открытых источниках"
 
    return {
        "achievement": achievement,
        "query_used": query,
        "status": status,
        "confidence": confidence,
        "message": message,
        "matching_urls": matching_urls[:3],
        "results_count": len([r for r in results if "error" not in r])
    }
 
 
# ═══════════════════════════════════════
# 3. ПРОВЕРКА GITHUB ПРОФИЛЯ
# ═══════════════════════════════════════
 
def check_github(github_username: str) -> dict:
    """
    Проверяет GitHub профиль через публичный API (без ключа).
    """
    if not github_username:
        return {"found": False, "message": "GitHub не указан"}
 
    # Убираем лишнее из ссылки
    username = github_username.strip("/").split("/")[-1].replace("@", "")
 
    try:
        # Получаем данные профиля
        profile_url = f"https://api.github.com/users/{username}"
        response = requests.get(profile_url, headers=HEADERS, timeout=10)
 
        if response.status_code == 404:
            return {
                "found": False,
                "username": username,
                "message": f"❌ GitHub профиль @{username} не найден"
            }
 
        profile = response.json()
 
        # Получаем репозитории
        repos_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5"
        repos_response = requests.get(repos_url, headers=HEADERS, timeout=10)
        repos = repos_response.json() if repos_response.status_code == 200 else []
 
        # Считаем звёзды
        total_stars = sum(r.get("stargazers_count", 0) for r in repos if isinstance(r, dict))
 
        # Оцениваем активность
        public_repos = profile.get("public_repos", 0)
        followers = profile.get("followers", 0)
 
        if public_repos >= 10 or total_stars >= 5:
            activity_level = "Высокая"
            activity_score = 15
        elif public_repos >= 3:
            activity_level = "Средняя"
            activity_score = 8
        else:
            activity_level = "Низкая"
            activity_score = 3
 
        top_repos = [
            {
                "name": r.get("name"),
                "description": r.get("description", ""),
                "stars": r.get("stargazers_count", 0),
                "language": r.get("language", ""),
            }
            for r in repos[:3] if isinstance(r, dict)
        ]
 
        return {
            "found": True,
            "username": username,
            "public_repos": public_repos,
            "followers": followers,
            "total_stars": total_stars,
            "activity_level": activity_level,
            "activity_score": activity_score,
            "top_repos": top_repos,
            "profile_url": f"https://github.com/{username}",
            "message": f"✅ GitHub найден: {public_repos} репо, {total_stars} ★, активность: {activity_level}"
        }
 
    except Exception as e:
        return {
            "found": False,
            "message": f"Ошибка проверки GitHub: {e}"
        }
 
 
# ═══════════════════════════════════════
# 4. ГЛАВНАЯ ФУНКЦИЯ — ПОЛНАЯ ПРОВЕРКА
# ═══════════════════════════════════════
 
def check_web_footprint(
    candidate_name: str,
    achievements: list[dict] = None,
    github_username: str = None,
    linkedin_url: str = None
) -> dict:
    """
    Полная проверка браузерного следа кандидата.
 
    achievements: [
        {"title": "1 место чемпионат Казахстана по программированию", "year": "2023"},
        {"title": "Победитель олимпиады по математике", "year": "2022"},
    ]
    """
    results = {
        "candidate": candidate_name,
        "github": None,
        "achievements_verified": [],
        "overall_trust": "Низкий",
        "summary": ""
    }
 
    # Проверяем GitHub
    if github_username:
        results["github"] = check_github(github_username)
 
    # Проверяем каждое достижение
    confirmed = 0
    partial = 0
 
    if achievements:
        for ach in achievements:
            title = ach.get("title", "")
            year = ach.get("year", "")
            if title:
                verification = verify_achievement(candidate_name, title, year)
                results["achievements_verified"].append(verification)
 
                if verification["status"] == "confirmed":
                    confirmed += 1
                elif verification["status"] == "partial":
                    partial += 1
 
                time.sleep(1)  # пауза между запросами
 
    # Общий уровень доверия
    total_checked = len(results["achievements_verified"])
    if total_checked == 0:
        trust = "Не проверялось"
    elif confirmed >= total_checked * 0.7:
        trust = "Высокий"
    elif confirmed + partial >= total_checked * 0.5:
        trust = "Средний"
    else:
        trust = "Низкий"
 
    results["overall_trust"] = trust
 
    # Краткое резюме
    github_msg = results["github"]["message"] if results["github"] else "GitHub не указан"
    results["summary"] = (
        f"Браузерный след: {candidate_name}\n"
        f"  GitHub: {github_msg}\n"
        f"  Достижений проверено: {total_checked}\n"
        f"  Подтверждено: {confirmed} | Частично: {partial} | Не найдено: {total_checked - confirmed - partial}\n"
        f"  Общий уровень доверия: {trust}"
    )
 
    return results