from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil

# Импортируем твою логику из соседнего модуля
# Важно: запускать uvicorn нужно из корня или папки src
from src.ai_modules.evaluator import evaluate_candidate
from src.ai_modules.file_reader import read_file

app = FastAPI(
    title="IUAA API",
    description="Интеллектуальный ассистент приемной комиссии InVision U",
    version="1.0.0"
)

# Модель для текстового ввода (например, из формы эссе)
class EssaySubmission(BaseModel):
    candidate_name: str
    essay_text: str

# Модель ответа (теперь более детальная)
class AnalysisResult(BaseModel):
    candidate_name: str
    raw_analysis: str  # Полный текст от DeepSeek с баллами

@app.get("/")
async def root():
    return {"status": "online", "project": "IUAA", "case": "Invision U"}

@app.post("/analyze-text", response_model=AnalysisResult)
async def analyze_text(submission: EssaySubmission):
    """Эндпоинт для прямого анализа текста эссе"""
    if not submission.essay_text:
        raise HTTPException(status_code=400, detail="Текст эссе пуст")
    
    try:
        # Вызываем реальную функцию из evaluator.py
        analysis = evaluate_candidate(submission.essay_text)
        return AnalysisResult(
            candidate_name=submission.candidate_name,
            raw_analysis=analysis
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка ИИ: {str(e)}")

@app.post("/analyze-file")
async def analyze_upload(candidate_name: str, file: UploadFile = File(...)):
    """Эндпоинт для загрузки PDF/DOCX файлов"""
    # Создаем временную папку для сохранения файла
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. Читаем файл через твой file_reader.py
        text = read_file(file_path)
        
        # 2. Оцениваем текст через твой evaluator.py
        analysis = evaluate_candidate(text)
        
        return {
            "candidate_name": candidate_name,
            "filename": file.filename,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")
    finally:
        # Удаляем временный файл
        if os.path.exists(file_path):
            os.remove(file_path)