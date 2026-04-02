import sys
import os
import shutil
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
 
# Настройка путей
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))
 
from src.ai_modules.file_reader import read_file
from src.ai_modules.evaluator import evaluate_candidate
from src.ai_modules.scorer import (
    score_school,
    score_certificate,
    score_achievements,
    score_essay,
    compute_total_score,
    rank_candidates
)
from src.ai_modules.web_footprint import check_web_footprint
 
app = FastAPI(title="InVision U - AI Detective API")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    level: str      # international / national / regional / school
    category: str   # academic / sport / arts / volunteer / other
    year: Optional[str] = ""
 
class CandidateFullProfile(BaseModel):
    candidate_name: str
    essay_text: str
    school_name: str
    gpa: float                          # 1.0 - 5.0
    cert_type: str                      # IELTS, TOEFL, UNT, DUOLINGO, SAT
    cert_score: float
    cert_valid: bool = True
    cert_expired: bool = False
    test_date: Optional[str] = None
    achievements: Optional[List[Achievement]] = []
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
 
 
# ═══════════════════════════════════════
# ЭНДПОИНТЫ
# ═══════════════════════════════════════
 
@app.get("/")
async def health_check():
    return {"status": "online", "message": "IUAA AI Detective is running"}
 
 
# --- 1. Анализ эссе + файла сертификата ---
@app.post("/analyze")
async def analyze_candidate(
    candidate_name: str = Form(...),
    test_date: str = Form("2024-01-01"),
    cert_type: str = Form("OTHER"),
    file: UploadFile = File(...)
):
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    temp_path = os.path.join(TEMP_DIR, f"{file_id}{ext}")
 
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
 
        try:
            extracted_text = read_file(temp_path)
        except Exception:
            extracted_text = "Текст не извлечён (изображение сертификата)"
 
        # evaluate_candidate возвращает (report_text, scores_dict)
        report, scores = evaluate_candidate(
            text=extracted_text,
            cert_file=temp_path,
            test_date=test_date,
            cert_type=cert_type
        )
 
        return {
            "candidate": candidate_name,
            "status": "success",
            "ai_report": report,
            "ai_scores": scores
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
 
 
# --- 2. Полный скоринг одного кандидата (JSON) ---
@app.post("/score")
async def score_candidate(profile: CandidateFullProfile):
    try:
        # Шаг 1: LLM анализ эссе → получаем текст + баллы
        ai_report, ai_scores = evaluate_candidate(
            text=profile.essay_text,
            test_date=profile.test_date,
            cert_type=profile.cert_type
        )
 
        leadership   = ai_scores.get("leadership", 5)
        growth       = ai_scores.get("growth", 5)
        authenticity = ai_scores.get("authenticity", 5)
 
        # Шаг 2: Скоринг по блокам
        school_result = score_school(profile.school_name, profile.gpa)
 
        cert_result = score_certificate(
            cert_type=profile.cert_type,
            cert_score=profile.cert_score,
            cert_valid=profile.cert_valid,
            cert_expired=profile.cert_expired
        )
 
        achievement_list = [
            {"title": a.title, "level": a.level, "category": a.category}
            for a in (profile.achievements or [])
        ]
        achievement_result = score_achievements(achievement_list)
        essay_result = score_essay(leadership, growth, authenticity)
 
        # Шаг 3: Итоговый балл
        total = compute_total_score(
            school_result=school_result,
            cert_result=cert_result,
            achievement_result=achievement_result,
            essay_result=essay_result,
            candidate_name=profile.candidate_name
        )
 
        # Шаг 4: Браузерный след
        web_result = None
        if profile.github_username or profile.achievements:
            achievements_to_check = [
                {"title": a.title, "year": a.year}
                for a in (profile.achievements or [])
            ]
            web_result = check_web_footprint(
                candidate_name=profile.candidate_name,
                achievements=achievements_to_check,
                github_username=profile.github_username
            )
 
        return {
            "status": "ok",
            "scoring": total,
            "ai_scores": ai_scores,
            "web_footprint": web_result,
            "ai_report": ai_report
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
 
 
# --- 3. Рейтинг нескольких кандидатов ---
@app.post("/rank")
async def rank_multiple_candidates(profiles: List[CandidateFullProfile]):
    if len(profiles) < 2:
        raise HTTPException(status_code=400, detail="Нужно минимум 2 кандидата")
    if len(profiles) > 20:
        raise HTTPException(status_code=400, detail="Максимум 20 кандидатов")
 
    try:
        all_scores = []
 
        for profile in profiles:
            # Для /rank используем дефолтные баллы эссе (5/5/5)
            # чтобы не ждать LLM для каждого кандидата
            school_result = score_school(profile.school_name, profile.gpa)
            cert_result = score_certificate(
                cert_type=profile.cert_type,
                cert_score=profile.cert_score,
                cert_valid=profile.cert_valid,
                cert_expired=profile.cert_expired
            )
            achievement_list = [
                {"title": a.title, "level": a.level, "category": a.category}
                for a in (profile.achievements or [])
            ]
            achievement_result = score_achievements(achievement_list)
            essay_result = score_essay(5, 5, 5)  # нейтральный дефолт
 
            total = compute_total_score(
                school_result=school_result,
                cert_result=cert_result,
                achievement_result=achievement_result,
                essay_result=essay_result,
                candidate_name=profile.candidate_name
            )
            all_scores.append(total)
 
        ranked = rank_candidates(all_scores)
        return {
            "status": "ok",
            "total_candidates": len(ranked),
            "ranking": ranked
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка ранжирования: {str(e)}")
 
 
# --- 4. Только браузерный след ---
@app.post("/web-check")
async def web_check(
    candidate_name: str = Form(...),
    github_username: str = Form(""),
    achievements_json: str = Form("[]")
):
    import json
    try:
        achievements = json.loads(achievements_json)
        result = check_web_footprint(
            candidate_name=candidate_name,
            achievements=achievements,
            github_username=github_username or None
        )
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
 