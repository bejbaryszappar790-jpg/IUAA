"""
scorer.py — Модуль взвешенного скоринга кандидатов InVision U
 
Логика: троечник из элитной школы > отличник из обычной школы
Итоговый балл: 100 очков максимум
"""
 
# ═══════════════════════════════════════
# СПИСОК ЭЛИТНЫХ ШКОЛ КАЗАХСТАНА
# ═══════════════════════════════════════
 
ELITE_SCHOOLS = {
    # NIS — Назарбаев Интеллектуальные Школы
    "nis": 1.4,
    "назарбаев интеллектуальная школа": 1.4,
    "nazarbayev intellectual school": 1.4,
 
    # БИЛ — Билим-Инновация Лицей
    "бил": 1.3,
    "билим инновация": 1.3,
    "bil": 1.3,
    "bilim innovation": 1.3,
 
    # РФМШ — Республиканская физмат школа
    "рфмш": 1.35,
    "республиканская физико-математическая школа": 1.35,
    "rfmsh": 1.35,
 
    # Mektep / Bolashak
    "mektep": 1.25,
    "мектеп": 1.25,
    "bolashak": 1.25,
    "болашак": 1.25,
 
    # Международные школы в Казахстане
    "haileybury": 1.3,
    "мирас": 1.2,
    "miras": 1.2,
    "ist": 1.2,
    "international school": 1.2,
}
 
# ═══════════════════════════════════════
# ВЕСА БЛОКОВ (итого = 100)
# ═══════════════════════════════════════
 
WEIGHTS = {
    "school":       25,   # Школа + оценки (с множителем)
    "certificate":  30,   # Сертификаты (IELTS, UNT и т.д.)
    "achievements": 25,   # Спорт, олимпиады, достижения
    "essay":        20,   # Качество эссе (от LLM)
}
 
# ═══════════════════════════════════════
# 1. СКОРИНГ ШКОЛЫ
# ═══════════════════════════════════════
 
def score_school(school_name: str, gpa: float) -> dict:
    """
    gpa: средний балл от 1.0 до 5.0 (казахстанская система)
    school_name: название школы
 
    Логика: элитная школа с 3.0 > обычная школа с 5.0
    """
    school_lower = school_name.lower().strip()
 
    # Определяем множитель школы
    multiplier = 1.0  # обычная школа
    school_tier = "Обычная школа"
 
    for keyword, mult in ELITE_SCHOOLS.items():
        if keyword in school_lower:
            multiplier = mult
            school_tier = f"Элитная школа (×{mult})"
            break
 
    # Базовый балл за GPA (0-100)
    # 5.0 → 100, 4.0 → 75, 3.0 → 50, 2.0 → 25
    base_gpa_score = max(0, min(100, (gpa - 1.0) / 4.0 * 100))
 
    # Применяем множитель школы
    raw_score = base_gpa_score * multiplier
 
    # Нормализуем в диапазон 0-25 (вес блока)
    final_score = min(WEIGHTS["school"], raw_score / 100 * WEIGHTS["school"] * multiplier)
    final_score = round(min(final_score, WEIGHTS["school"]), 1)
 
    return {
        "score": final_score,
        "max": WEIGHTS["school"],
        "school_tier": school_tier,
        "multiplier": multiplier,
        "gpa": gpa,
        "explanation": f"Школа: {school_name} ({school_tier}), GPA: {gpa}/5.0 → {final_score}/{WEIGHTS['school']} баллов"
    }
 
 
# ═══════════════════════════════════════
# 2. СКОРИНГ СЕРТИФИКАТОВ
# ═══════════════════════════════════════
 
CERT_SCORES = {
    # IELTS
    "ielts": {
        (7.0, 9.0): 30,
        (6.0, 6.9): 22,
        (5.0, 5.9): 14,
        (0.0, 4.9): 5,
    },
    # TOEFL iBT
    "toefl": {
        (100, 120): 30,
        (80,  99):  22,
        (60,  79):  14,
        (0,   59):  5,
    },
    # Duolingo
    "duolingo": {
        (120, 160): 28,
        (100, 119): 20,
        (0,   99):  10,
    },
    # UNT
    "unt": {
        (120, 140): 30,
        (100, 119): 22,
        (80,   99): 14,
        (0,    79): 5,
    },
    # SAT
    "sat": {
        (1400, 1600): 30,
        (1200, 1399): 22,
        (1000, 1199): 14,
        (0,     999): 5,
    },
}
 
def score_certificate(cert_type: str, cert_score: float, cert_valid: bool, cert_expired: bool) -> dict:
    """
    cert_type: 'IELTS', 'TOEFL', 'UNT', 'DUOLINGO', 'SAT'
    cert_score: числовой балл сертификата
    cert_valid: прошёл ли QR-проверку
    cert_expired: истёк ли срок
    """
    cert_lower = cert_type.lower().strip()
    ranges = CERT_SCORES.get(cert_lower)
 
    if not ranges:
        return {
            "score": 0,
            "max": WEIGHTS["certificate"],
            "explanation": f"Неизвестный тип сертификата: {cert_type}"
        }
 
    # Находим базовый балл по диапазону
    base = 0
    for (low, high), points in ranges.items():
        if low <= cert_score <= high:
            base = points
            break
 
    # Штрафы
    if cert_expired:
        base = max(0, base - 15)
        penalty_note = " | ⚠️ Просрочен (-15)"
    elif not cert_valid:
        base = max(0, base - 10)
        penalty_note = " | ⚠️ QR не подтверждён (-10)"
    else:
        penalty_note = " | ✅ Подтверждён"
 
    final_score = round(min(base, WEIGHTS["certificate"]), 1)
 
    return {
        "score": final_score,
        "max": WEIGHTS["certificate"],
        "explanation": f"{cert_type}: {cert_score} → {final_score}/{WEIGHTS['certificate']} баллов{penalty_note}"
    }
 
 
# ═══════════════════════════════════════
# 3. СКОРИНГ ДОСТИЖЕНИЙ
# ═══════════════════════════════════════
 
ACHIEVEMENT_LEVELS = {
    "international": 25,   # Международные олимпиады, чемпионаты мира
    "national":      18,   # Национальный уровень
    "regional":      11,   # Областной / городской
    "school":         5,   # Школьный уровень
    "none":           0,
}
 
ACHIEVEMENT_CATEGORIES = {
    "academic":  1.0,   # Олимпиады, наука
    "sport":     0.85,  # Спорт
    "arts":      0.8,   # Искусство, музыка
    "volunteer": 0.75,  # Волонтёрство, социальные проекты
    "other":     0.7,
}
 
def score_achievements(achievements: list[dict]) -> dict:
    """
    achievements: список словарей вида:
    [
        {"title": "Олимпиада по математике", "level": "national", "category": "academic"},
        {"title": "Чемпион по боксу", "level": "international", "category": "sport"},
    ]
    """
    if not achievements:
        return {
            "score": 0,
            "max": WEIGHTS["achievements"],
            "explanation": "Достижения не указаны → 0 баллов"
        }
 
    total = 0
    breakdown = []
 
    for ach in achievements:
        level = ach.get("level", "none").lower()
        category = ach.get("category", "other").lower()
        title = ach.get("title", "Без названия")
 
        level_score = ACHIEVEMENT_LEVELS.get(level, 0)
        category_mult = ACHIEVEMENT_CATEGORIES.get(category, 0.7)
        points = round(level_score * category_mult, 1)
        total += points
        breakdown.append(f"  • {title} ({level}, {category}) → +{points}")
 
    # Нормализуем: максимум = вес блока
    final_score = round(min(total, WEIGHTS["achievements"]), 1)
 
    return {
        "score": final_score,
        "max": WEIGHTS["achievements"],
        "breakdown": breakdown,
        "explanation": "Достижения:\n" + "\n".join(breakdown) + f"\nИтого: {final_score}/{WEIGHTS['achievements']}"
    }
 
 
# ═══════════════════════════════════════
# 4. СКОРИНГ ЭССЕ (от LLM)
# ═══════════════════════════════════════
 
def score_essay(leadership: int, growth: int, authenticity: int) -> dict:
    """
    Принимает баллы от LLM (каждый 0-10) и конвертирует в вес блока (0-20)
    """
    raw = leadership + growth + authenticity  # max = 30
    final_score = round((raw / 30) * WEIGHTS["essay"], 1)
 
    return {
        "score": final_score,
        "max": WEIGHTS["essay"],
        "leadership": leadership,
        "growth": growth,
        "authenticity": authenticity,
        "explanation": f"Лидерство {leadership}/10 + Рост {growth}/10 + Подлинность {authenticity}/10 → {final_score}/{WEIGHTS['essay']}"
    }
 
 
# ═══════════════════════════════════════
# 5. ИТОГОВЫЙ СКОРИНГ КАНДИДАТА
# ═══════════════════════════════════════
 
def compute_total_score(
    school_result: dict,
    cert_result: dict,
    achievement_result: dict,
    essay_result: dict,
    candidate_name: str = "Кандидат"
) -> dict:
    """
    Собирает итоговый балл и формирует объяснение для комиссии.
    """
    total = (
        school_result["score"] +
        cert_result["score"] +
        achievement_result["score"] +
        essay_result["score"]
    )
    total = round(min(total, 100), 1)
 
    # Уровень доверия
    if total >= 75:
        trust = "Высокий"
    elif total >= 50:
        trust = "Средний"
    else:
        trust = "Низкий"
 
    return {
        "candidate": candidate_name,
        "total_score": total,
        "max_score": 100,
        "trust_level": trust,
        "breakdown": {
            "school":       school_result,
            "certificate":  cert_result,
            "achievements": achievement_result,
            "essay":        essay_result,
        },
        "summary": (
            f"{candidate_name}: {total}/100 | Доверие: {trust}\n"
            f"  Школа:        {school_result['score']}/{WEIGHTS['school']}\n"
            f"  Сертификат:   {cert_result['score']}/{WEIGHTS['certificate']}\n"
            f"  Достижения:   {achievement_result['score']}/{WEIGHTS['achievements']}\n"
            f"  Эссе:         {essay_result['score']}/{WEIGHTS['essay']}"
        )
    }
 
 
# ═══════════════════════════════════════
# 6. СРАВНЕНИЕ НЕСКОЛЬКИХ КАНДИДАТОВ
# ═══════════════════════════════════════
 
def rank_candidates(candidates: list[dict]) -> list[dict]:
    """
    Принимает список итоговых результатов compute_total_score()
    Возвращает отсортированный рейтинг с местами.
    """
    sorted_candidates = sorted(
        candidates,
        key=lambda x: x["total_score"],
        reverse=True
    )
 
    for i, candidate in enumerate(sorted_candidates):
        candidate["rank"] = i + 1
 
    return sorted_candidates