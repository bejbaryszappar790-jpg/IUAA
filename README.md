# IUAA: InVision U Admission Assistant 🚀

**Интеллектуальная система автоматизированного пре-скрининга и экспертной оценки абитуриентов на базе DeepSeek-R1.**

Разработано в рамках хакатона **Decentrathon 5.0** (Трек: AI inDrive / Invision U).

---

## 📌 Обзор проекта
**IUAA** — это инновационное решение для приемных комиссий, позволяющее объективно оценивать потенциал кандидатов в условиях массового использования генеративного ИИ. Система анализирует не форму, а содержание, выявляя реальные достижения и Soft Skills.

🧠 Skeptical AI Evaluator

Промпт-инжиниринг на основе evidence-based scoring. LLM (DeepSeek-R1 через Ollama) ищет конкретные доказательства, а не общие фразы. Автоматически детектирует шаблонные ответы и выставляет баллы по 4 критериям:

    Опыт (лидерство и командная работа)

    Потенциал (анализ сочетания предметов ЕНТ)

    Рост (конкретность мотивации и саморазвития)

    Подлинность документов (QR-коды, сроки действия)

📄 Интеллектуальный парсинг

    Поддержка PDF, DOCX, изображений (JPG/PNG)

    Извлечение текста через pdfplumber и python-docx

    Для изображений — проверка QR-кодов через OpenCV

🔐 Верификация сертификатов (cert_val.py)

    Распознавание QR-кодов на сертификатах (IELTS, TOEFL, Duolingo, UNT, SAT)

    Проверка срока действия (базово 2 года)

    Автоматические штрафы за просрочку или отсутствие QR

⚖️ Взвешенный скоринг (scorer.py)

Логика: троечник из элитной школы > отличник из обычной школы
Блок	Вес
🏫 Школа + GPA	25
📜 Сертификаты	30
🏆 Достижения	25
✍️ Эссе	20
Итого	100

Элитные школы Казахстана (с повышающим коэффициентом):

    НИШ (×1.4) | РФМШ (×1.35) | БИЛ (×1.3) | Haileybury (×1.3) | Мирас (×1.2)

🌐 Цифровой след (web_footprint.py)

    🔍 Поиск достижений через DuckDuckGo (без API-ключа)

    🧠 Анализ совпадений (имя кандидата + событие)

    🐙 Проверка GitHub профиля (количество репозиториев, активность)

    🛡️ Rate limiting + резервный ручной парсинг HTML

    📊 Итоговый уровень доверия: Высокий / Средний / Низкий

⚡ Production-ready API

Асинхронный FastAPI с эндпоинтами:

    POST /analyze — анализ эссе + файла сертификата

    POST /score — полный скоринг по JSON-профилю

    POST /rank — рейтинг нескольких кандидатов

    POST /web-check — только браузерный след

---

## 🏗 Архитектура системы (Clean Architecture)

## Фронтенд слой (models/my-ai-detective/)

    Технологии: Next.js 14 (App Router), TypeScript, Tailwind CSS

    Роль: Веб-интерфейс для приемной комиссии

    Взаимодействие: HTTP запросы к api/main.py (localhost:8000)

## API слой (api/main.py)

    Роль: Точка входа, HTTP обработчики, валидация

    Эндпоинты:

        POST /analyze → загрузка файлов + AI анализ

        POST /score → JSON профиль → полный скоринг

        POST /rank → несколько кандидатов → рейтинг

        POST /web-check → только цифровой след

    Особенности: CORS middleware, временное хранилище (UUID), асинхронность

## AI модули (src/ai_modules/)

**Связаны через цепочку вызовов:**

text

main.py (эндпоинт)
    ↓ вызывает
evaluator.evaluate_candidate()
    ↓ вызывает
prompts.build_full_prompt() + cert_val.verify_certificate()
    ↓ отправляет запрос в
Ollama API (локально, модель DeepSeek-R1)
    ↓ возвращает
LLM ответ → extract_scores() → (experience, growth, potential, authenticity)
    ↓ передает в
scorer.score_essay() → скоринг 20 баллов

**Параллельно:**
text

main.py (эндпоинт /score)
    ↓ вызывает
scorer.score_school()      → 25 баллов
scorer.score_certificate() → 30 баллов
scorer.score_achievements()→ 25 баллов
scorer.score_essay()       → 20 баллов
    ↓ суммирует
compute_total_score() → 0-100 баллов

## Хранилища

    temp_storage/ — временные файлы (автоочистка после обработки)

    data/synthetic/ — тестовые данные (PDF, DOCX, изображения)

    models/ollama_config.json — параметры LLM (temperature, top_p, таймауты)

## Утилиты

    file_reader.py → унифицированный интерфейс для PDF/DOCX/Image

    cert_val.py → OpenCV + pyzbar для QR-кодов

    web_footprint.py → DuckDuckGo поиск + GitHub API

---

## 🛠 Технологический стек
**Компонент:**	Технологии
**Backend:**	Python 3.12+, FastAPI, Uvicorn
**LLM:**	DeepSeek-R1 (8B) через Ollama API
**Документы**	pdfplumber, python-docx, opencv-python, pyzbar
**Веб-поиск**	duckduckgo-search, requests, re
**Валидация**	Pydantic
**Инфраструктура**	Git, Virtualenv

---

## 📂 Структура репозитория
```text
IUAA/
├── data/
│   └── synthetic/              
├── models/
│   ├── ollama_config.json
│   └── my-ai-detective/
│       ├── .next/
│       ├── app/
│       ├── node_modules/
│       ├── public/
│       ├── src/
│       ├── .gitignore
│       ├── AGENTS.md
│       ├── CLAUDE.md
│       ├── eslint.config.mjs
│       ├── next-env.d.ts
│       ├── next.config.ts
│       ├── package-lock.json
│       ├── package.json
│       ├── postcss.config.mjs
│       ├── README.md
│       └── tsconfig.json
├── notebooks/
├── src/
│   ├── ai_modules/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── cert_val.py
│   ├── evaluator.py
│   ├── file_reader.py
│   ├── prompts.py
│   ├── scorer.py
│   └── web_footprint.py
├── api/
│   ├── __pycache__/
│   ├── __init__.py
│   └── main.py
├── temp_storage/
├── temp_updates/
├── .gitignore
├── all_code.txt
├── all_mys_code.txt
├── final_check_code.txt
├── iuaa_deepseek.py
├── README.md
└── requirements.txt



# Создание и активация виртуального окружения
python3 -m venv .venv
source .venv/bin/activate

# Установка всех необходимых библиотек
pip install -r requirements.txt



# Запуск из корня проекта
uvicorn src.api.main:app --reload


Интерактивная документация API (Swagger) доступна по адресу: http://127.0.0.1:8000/docs

## 👥 Команда проекта: **2Bros**

* **Beibarys** — Backend Developer / System Architect (FastAPI, Infrastructure)
* **Harun** — AI/ML Engineer (Prompt Engineering, LLM Integration)

---

## 🎯 Почему наше решение эффективно?

> **В условиях, когда каждый абитуриент может использовать ChatGPT для написания эссе, стандартные методы отбора перестают работать.** **IUAA** меняет парадигму: мы используем аналитическую мощность **DeepSeek-R1**, чтобы находить «зерна» реального опыта в «плевелах» сгенерированного текста. Это гарантирует университету выбор действительно талантливых и искренних студентов, а не тех, кто лучше всех владеет нейросетями.