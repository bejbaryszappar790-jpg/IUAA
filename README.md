# IUAA: InVision U's Admission Assistant 🚀

**Интеллектуальная система поддержки принятия решений для автоматизации и объективизации отбора абитуриентов.**

Разработано в рамках хакатона **Decentrathon 5.0** (Трек: AI inDrive).

---

## 📌 Обзор проекта
IUAA (InVision U Admission Assistant) — это инструмент для приемных комиссий университетов, решающий проблему субъективности и "информационного шума" при анализе тысяч заявок.

### Ключевые функции:
* **🛡 Детекция AI-контента:** Выявление текстов, сгенерированных LLM (ChatGPT и др.), для обеспечения честной конкуренции.
* **📈 Экстракция Soft Skills:** Автоматический анализ лидерского потенциала и мотивации через NLP-модели.
* **⚖️ Unbiased AI:** Исключение гендерных и региональных признаков из скоринга для обеспечения равных возможностей.
* **🔍 Explainable AI (XAI):** Каждая рекомендация сопровождается текстовым обоснованием принятого решения.

---

## 🏗 Архитектура системы
* **AI Core (`/src/ai`)**: Local DeepSeek R1 7B by Ollama.
* **Backend (`/src/api`)**: API на **FastAPI**, обеспечивающий связь моделей с интерфейсом.
* **Frontend (`/src/ui`)**: Интерактивный дашборд на **Flutter Web**.

---

## 🛠 Технологический стек
* **Языки:** Python 3.13 (3.12), Dart
* **Frameworks:** FastAPI, Flutter Web
* **AI/ML:** Local Ollama (DeepSeek R1 7B)
* **Infrastructure:** venv, Git

---

## 📂 Структура репозитория
```text
IUAA/
├── .venv/               # Виртуальное окружение (игнорируется Git)
├── src/
│   ├── api/             # Бэкенд логика
│   ├── ai/              # ML-модели и скрипты
│   └── ui/              # Код Flutter приложения
├── data/                # Синтетические данные (JSON)
├── requirements.txt     # Зависимости проекта
└── README.md            # Документация



# Создание и активация окружения
python3 -m venv .venv
source .venv/bin/activate

# Обновление pip и установка зависимостей
python -m pip install --upgrade pip
pip install -r requirements.txt

# Запуск сервера
python -m uvicorn src.api.main:app --reload



cd src/ui
flutter pub get
flutter run -d chrome


Команда:

Beybaris — Backend Developer / System Architect
Harun — AI/ML Engineer
