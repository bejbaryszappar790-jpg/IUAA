"""
scorer.py — Модуль взвешенного скоринга кандидатов InVision U (Исправленная версия)
Логика: троечник из элитной школы > отличник из обычной школы
Итоговый балл: 100 очков максимум
"""

# ═══════════════════════════════════════
# СПИСОК ЭЛИТНЫХ ШКОЛ КАЗАХСТАНА
# ═══════════════════════════════════════
ELITE_SCHOOLS = {
    "nis": 1.4,
    "назарбаев интеллектуальная школа": 1.4,
    "nazarbayev intellectual school": 1.4,
    "бил": 1.3,
    "билим инновация": 1.3,
    "bil": 1.3,
    "bilim innovation": 1.3,
    "рфмш": 1.35,
    "республиканская физико-математическая школа": 1.35,
    "rfmsh": 1.35,
    "mektep": 1.25,
    "мектеп": 1.25,
    "bolashak": 1.25,
    "болашак": 1.25,
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
    "school":       25,   # Школа + оценки
    "certificate":  30,   # Сертификаты
    "achievements": 25,   # Достижения
    "essay":        20,   # Эссе
}

# ═══════════════════════════════════════
# 1. СКОРИНГ ШКОЛЫ
# ═══════════════════════════════════════
def score_school(school_name: str, gpa: float) -> dict:
    school_lower = school_name.lower().strip()
    multiplier = 1.0
    school_tier = "Обычная школа"

    for keyword, mult in ELITE_SCHOOLS.items():
        if keyword in school_lower:
            multiplier = mult
            school_tier = f"Элитная школа (×{mult})"
            break

    # Базовый балл за GPA (0-100)
    base_gpa_score = max(0, min(100, (gpa - 1.0) / 4.0 * 100))

    # ПРИМЕНЯЕМ МНОЖИТЕЛЬ (Исправлено: теперь множитель не дублируется)
    # Считаем процент от веса блока (25) с учетом коэффициента школы
    final_score = (base_gpa_score / 100) * WEIGHTS["school"] * multiplier
    
    # Ограничиваем максимумом блока, но даем элитным школам преимущество
    final_score = round(min(final_score, WEIGHTS["school"] * (multiplier if multiplier > 1 else 1)), 1)
    # Чтобы итоговая сумма не улетела выше 100, жестко ограничиваем весом блока
    final_score = min(final_score, float(WEIGHTS["school"]))

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
    "ielts": {(7.0, 9.0): 30, (6.0, 6.9): 22, (5.0, 5.9): 14, (0.0, 4.9): 5},
    "toefl": {(100, 120): 30, (80, 99): 22, (60, 79): 14, (0, 59): 5},
    "duolingo": {(120, 160): 28, (100, 119): 20, (0, 99): 10},
    "unt": {(120, 140): 30, (100, 119): 22, (80, 99): 14, (0, 79): 5},
    "sat": {(1400, 1600): 30, (1200, 1399): 22, (1000, 1199): 14, (0, 999): 5},
}

def score_certificate(cert_type: str, cert_score: float, cert_valid: bool, cert_expired: bool) -> dict:
    cert_lower = cert_type.lower().strip()
    ranges = CERT_SCORES.get(cert_lower)

    if not ranges:
        return {"score": 0, "max": WEIGHTS["certificate"], "explanation": f"Неизвестный тип: {cert_type}"}

    base = 0
    for (low, high), points in ranges.items():
        if low <= cert_score <= high:
            base = points
            break

    penalty_note = " | ✅ Подтверждён"
    if cert_expired:
        base = max(0, base - 15)
        penalty_note = " | ⚠️ Просрочен (-15)"
    elif not cert_valid:
        base = max(0, base - 10)
        penalty_note = " | ⚠️ QR не подтверждён (-10)"

    final_score = round(min(base, WEIGHTS["certificate"]), 1)
    return {
        "score": final_score,
        "max": WEIGHTS["certificate"],
        "explanation": f"{cert_type}: {cert_score} → {final_score}/{WEIGHTS['certificate']} баллов{penalty_note}"
    }

# ═══════════════════════════════════════
# 3. СКОРИНГ ДОСТИЖЕНИЙ
# ═══════════════════════════════════════
ACHIEVEMENT_LEVELS = {"international": 25, "national": 18, "regional": 11, "school": 5, "none": 0}
ACHIEVEMENT_CATEGORIES = {"academic": 1.0, "sport": 0.85, "arts": 0.8, "volunteer": 0.75, "other": 0.7}

def score_achievements(achievements: list[dict]) -> dict:
    if not achievements:
        return {"score": 0, "max": WEIGHTS["achievements"], "explanation": "Нет достижений"}

    total = 0
    breakdown = []
    for ach in achievements:
        level = ach.get("level", "none").lower()
        cat = ach.get("category", "other").lower()
        title = ach.get("title", "Без названия")
        points = round(ACHIEVEMENT_LEVELS.get(level, 0) * ACHIEVEMENT_CATEGORIES.get(cat, 0.7), 1)
        total += points
        breakdown.append(f"  • {title} ({level}) → +{points}")

    final_score = round(min(total, WEIGHTS["achievements"]), 1)
    return {
        "score": final_score, 
        "max": WEIGHTS["achievements"], 
        "explanation": f"Итого за достижения: {final_score}/{WEIGHTS['achievements']}"
    }

# ═══════════════════════════════════════
# 4. СКОРИНГ ЭССЕ
# ═══════════════════════════════════════
def score_essay(leadership: int, growth: int, authenticity: int) -> dict:
    raw = leadership + growth + authenticity
    final_score = round((raw / 30) * WEIGHTS["essay"], 1)
    return {
        "score": final_score,
        "max": WEIGHTS["essay"],
        "explanation": f"Лидерство {leadership}, Рост {growth}, Подлинность {authenticity} → {final_score}/{WEIGHTS['essay']}"
    }

# ═══════════════════════════════════════
# 5. ИТОГОВЫЙ СКОРИНГ
# ═══════════════════════════════════════
def compute_total_score(school_result, cert_result, achievement_result, essay_result, candidate_name="Кандидат"):
    total = round(school_result["score"] + cert_result["score"] + achievement_result["score"] + essay_result["score"], 1)
    total = min(total, 100.0)
    trust = "Высокий" if total >= 75 else "Средний" if total >= 50 else "Низкий"
    
    return {
        "candidate": candidate_name,
        "total_score": total,
        "trust_level": trust,
        "summary": f"{candidate_name}: {total}/100 | Доверие: {trust}"
    }

def rank_candidates(candidates: list[dict]) -> list[dict]:
    sorted_candidates = sorted(candidates, key=lambda x: x["total_score"], reverse=True)
    for i, c in enumerate(sorted_candidates): c["rank"] = i + 1
    return sorted_candidates