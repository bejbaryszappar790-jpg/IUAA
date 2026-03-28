from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Инициализируем FastAPI
app = FastAPI(
    title="IUAA API",
    description="Assistant for InVision U Admission Committee",
    version="0.1.0"
)

# Описываем структуру данных, которую мы ждем от фронтенда (Flutter)
class EssaySubmission(BaseModel):
    candidate_name: str
    essay_text: str

# Описываем структуру ответа
class AnalysisResult(BaseModel):
    candidate_name: str
    ai_generated_probability: float
    detected_skills: List[str]
    recommendation: str

@app.get("/")
async def root():
    """Проверка работоспособности API"""
    return {"message": "IUAA Backend is running", "status": "active"}

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_essay(submission: EssaySubmission):
    """Эндпоинт для анализа эссе"""
    if not submission.essay_text:
        raise HTTPException(status_code=400, detail="Essay text is empty")

    # ТУТ БУДЕТ МАГИЯ ИИ (позже подключим модели из src/ai)
    # Пока возвращаем заглушку (Mock Data)
    return AnalysisResult(
        candidate_name=submission.candidate_name,
        ai_generated_probability=0.12,  # 12% вероятность ИИ
        detected_skills=["Leadership", "Analytical Thinking", "Proactivity"],
        recommendation="Highly Recommended for Interview"
    )