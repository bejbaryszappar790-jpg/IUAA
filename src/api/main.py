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

# Настройка путей
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

from src.ai_modules.file_reader import read_file
from src.ai_modules.evaluator import evaluate_candidate
from src.ai_modules.scorer import (
    score_school, score_certificate, score_achievements,
    score_essay, compute_total_score, rank_candidates
)
from src.ai_modules.web_footprint import check_web_footprint

app = FastAPI(title="InVision U - AI Detective API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_storage"
os.makedirs(TEMP_DIR, exist_ok=True)

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
    # Баллы эссе (опционально)
    essay_leadership: Optional[int] = None
    essay_growth: Optional[int] = None
    essay_authenticity: Optional[int] = None

@app.get("/")
async def health_check():
    return {"status": "online", "version": "MVP 1.0"}

@app.post("/analyze")
async def analyze_candidate(
    candidate_name: str = Form(...),
    test_date: str = Form(...),
    cert_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Эндпоинт для быстрой проверки файла (Сертификат/Эссе)"""
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    temp_file_path = os.path.join(TEMP_DIR, f"{file_id}{ext}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted_text = read_file(temp_file_path)
        
        # Если это изображение, extracted_text будет специальной меткой
        analysis_report = evaluate_candidate(
            text=extracted_text,
            cert_file=temp_file_path,
            test_date=test_date,
            cert_type=cert_type
        )

        return {
            "candidate": candidate_name,
            "ai_report": analysis_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/score")
async def score_candidate(profile: CandidateFullProfile):
    """Полный комплексный скоринг"""
    try:
        # 1. Веб-след (делаем параллельно или в начале)
        achievements_to_check = [{"title": a.title, "year": a.year} for a in (profile.achievements or [])]
        web_result = check_web_footprint(
            candidate_name=profile.candidate_name,
            achievements=achievements_to_check,
            github_username=profile.github_username
        )

        # 2. Анализ Эссе через ИИ
        ai_report = evaluate_candidate(
            text=profile.essay_text or "Текст не предоставлен",
            test_date=profile.test_date,
            cert_type=profile.cert_type
        )

        # 3. Скоринг блоков
        school_res = score_school(profile.school_name, profile.gpa)
        cert_res = score_certificate(profile.cert_type, profile.cert_score, profile.cert_valid, profile.cert_expired)
        
        # Конвертируем достижения для scorer
        ach_list = [{"title": a.title, "level": a.level, "category": a.category} for a in (profile.achievements or [])]
        ach_res = score_achievements(ach_list)

        # Если баллы не пришли в JSON, берем средние (Или можно парсить из ai_report)
        l, g, a = (profile.essay_leadership or 6, profile.essay_growth or 6, profile.essay_authenticity or 6)
        essay_res = score_essay(l, g, a)

        # 4. Финальный расчет
        final_calculation = compute_total_score(school_res, cert_res, ach_res, essay_res, profile.candidate_name)

        return {
            "candidate": profile.candidate_name,
            "total_score": final_calculation["total_score"],
            "trust_level": final_calculation["trust_level"],
            "detailed_scoring": final_calculation["breakdown"],
            "web_analysis": web_result,
            "ai_logic_explanation": ai_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка комплексного скоринга: {str(e)}")

@app.post("/rank")
async def rank_multiple(profiles: List[CandidateFullProfile]):
    # Твоя логика ранжирования отличная, оставляем
    # ... (код из твоего main.py)
    pass