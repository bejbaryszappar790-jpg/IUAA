import sys
import os
import shutil
import uuid
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# 1. Настройка путей
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

# 2. Импорт модулей
from src.ai_modules.file_reader import read_file
from src.ai_modules.evaluator import evaluate_candidate
from src.ai_modules.scorer import (
    score_school, score_certificate, score_achievements,
    score_essay, compute_total_score, rank_candidates
)
from src.ai_modules.web_footprint import check_web_footprint

app = FastAPI(title="InVision U - AI Detective API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_storage"
os.makedirs(TEMP_DIR, exist_ok=True)

# ═══════════════════════════════════════
# МОДЕЛИ ДАННЫХ
# ═══════════════════════════════════════

class Achievement(BaseModel):
    title: str
    level: str
    category: str
    year: Optional[str] = ""

class CandidateFullProfile(BaseModel):
    candidate_name: str
    essay_text: Optional[str] = ""
    school_name: str
    gpa: float
    cert_type: str
    cert_score: float
    cert_valid: bool = True
    cert_expired: bool = False
    test_date: Optional[str] = None
    achievements: Optional[List[Achievement]] = []
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    # Баллы эссе (опционально, если фронтенд хочет передать свои)
    essay_leadership: Optional[int] = None
    essay_growth: Optional[int] = None
    essay_authenticity: Optional[int] = None

# ═══════════════════════════════════════
# ЭНДПОИНТЫ
# ═══════════════════════════════════════

@app.get("/")
async def health_check():
    return {"status": "online", "version": "MVP 1.0 Final"}

@app.post("/analyze")
async def analyze_candidate(
    candidate_name: str = Form(...),
    test_date: str = Form(...),
    cert_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Анализ файла (скан сертификата или эссе)"""
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    temp_file_path = os.path.join(TEMP_DIR, f"{file_id}{ext}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted_text = read_file(temp_file_path)
        
        # ИСПРАВЛЕНИЕ: evaluator.py теперь возвращает (report, scores)
        analysis_report, ai_scores = evaluate_candidate(
            text=extracted_text,
            cert_file=temp_file_path,
            test_date=test_date,
            cert_type=cert_type
        )

        return {
            "candidate": candidate_name,
            "status": "ok",
            "ai_report": analysis_report,
            "ai_extracted_scores": ai_scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/score")
async def score_candidate(profile: CandidateFullProfile):
    """Полный скоринг с ИИ-анализом и веб-поиском"""
    try:
        # 1. Браузерный след (Web Footprint)
        achievements_to_check = [{"title": a.title, "year": a.year} for a in (profile.achievements or [])]
        web_result = check_web_footprint(
            candidate_name=profile.candidate_name,
            achievements=achievements_to_check,
            github_username=profile.github_username
        )

        # 2. ИИ анализ эссе и извлечение баллов
        # Передаем текст эссе. Если его нет — помечаем это.
        essay_content = profile.essay_text if profile.essay_text and len(profile.essay_text) > 10 else "[Текст эссе не предоставлен]"
        
        ai_report, ai_scores = evaluate_candidate(
            text=essay_content,
            test_date=profile.test_date,
            cert_type=profile.cert_type
        )

        # Решение Бага №1: используем баллы от ИИ, если они не переданы вручную
        leadership = profile.essay_leadership or ai_scores.get("leadership", 6)
        growth = profile.essay_growth or ai_scores.get("growth", 6)
        authenticity = profile.essay_authenticity or ai_scores.get("authenticity", 6)

        # 3. Расчет баллов по модулям
        school_res = score_school(profile.school_name, profile.gpa)
        cert_res = score_certificate(
            cert_type=profile.cert_type, 
            cert_score=profile.cert_score, 
            cert_valid=profile.cert_valid, 
            cert_expired=profile.cert_expired
        )
        
        ach_list = [{"title": a.title, "level": a.level, "category": a.category} for a in (profile.achievements or [])]
        ach_res = score_achievements(ach_list)
        
        essay_res = score_essay(leadership, growth, authenticity)

        # 4. Итоговый расчет (Explainable AI)
        final_calculation = compute_total_score(
            school_res, cert_res, ach_res, essay_res, profile.candidate_name
        )

        return {
            "status": "ok",
            "candidate": profile.candidate_name,
            "total_score": final_calculation["total_score"],
            "trust_level": final_calculation["trust_level"],
            "detailed_scoring": final_calculation["breakdown"],
            "web_analysis": web_result,
            "ai_detective_report": ai_report
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Ошибка скоринга: {str(e)}")

@app.post("/rank")
async def rank_multiple_candidates(profiles: List[CandidateFullProfile]):
    """Сравнение списка кандидатов"""
    try:
        all_scores = []
        for profile in profiles:
            # Для рейтинга делаем упрощенный скоринг (без повторного вызова ИИ для скорости)
            s_res = score_school(profile.school_name, profile.gpa)
            c_res = score_certificate(profile.cert_type, profile.cert_score, profile.cert_valid, profile.cert_expired)
            a_list = [{"title": a.title, "level": a.level, "category": a.category} for a in (profile.achievements or [])]
            a_res = score_achievements(a_list)
            
            # Берем баллы эссе из профиля или дефолт
            e_res = score_essay(profile.essay_leadership or 6, profile.essay_growth or 6, profile.essay_authenticity or 6)
            
            total = compute_total_score(s_res, c_res, a_res, e_res, profile.candidate_name)
            all_scores.append(total)

        ranked = rank_candidates(all_scores)
        return {"status": "ok", "ranking": ranked}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)