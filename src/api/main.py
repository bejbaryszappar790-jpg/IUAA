import sys
import os
import shutil
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

# 1. Настройка путей (чтобы API видел твои модули)
root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path))

# 2. Импорт твоих модулей и логики Харуна
from src.ai_modules.file_reader import read_file
from src.ai_modules.evaluator import evaluate_candidate

app = FastAPI(title="InVision U - Trust Engine API")

# Создаем папку для временных файлов, если её нет
TEMP_DIR = "temp_storage"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/")
async def health_check():
    return {"status": "online", "message": "IUAA Backend is running"}

@app.post("/analyze")
async def analyze_candidate(
    candidate_name: str = Form(...),
    test_date: str = Form(...),  # Ожидаем ГГГГ-ММ-ДД
    cert_type: str = Form(...),  # Например: IELTS, TOEFL, UNT
    file: UploadFile = File(...)
):
    # А. Сохраняем файл временно для обработки
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    temp_file_path = os.path.join(TEMP_DIR, f"{file_id}{ext}")

    try:
        # Сохраняем загруженный файл на диск
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Б. Извлекаем текст (через твой file_reader.py)
        try:
            extracted_text = read_file(temp_file_path)
        except Exception:
            # Если это картинка-сертификат без текста, просто ставим заглушку
            extracted_text = "Текст не извлечен (анализ изображения сертификата)"

        # В. ЗАПУСК ИИ (Вызов функции Харуна)
        # Мы передаем путь к файлу, чтобы cert_val.py мог найти QR-код
        analysis_report = evaluate_candidate(
            text=extracted_text,
            cert_file=temp_file_path,
            test_date=test_date,
            cert_type=cert_type
        )

        return {
            "candidate": candidate_name,
            "technical_status": "Processed",
            "ai_report": analysis_report
        }

    except Exception as e:
        # Если что-то пошло не так (например, Ollama не отвечает)
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")
    
    finally:
        # Г. Очистка: удаляем временный файл после обработки
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)