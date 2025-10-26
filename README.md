# AI Presentation Builder - Backend

**FastAPI-based REST API for AI-powered presentation generation**

A high-performance async backend service that leverages OpenAI for content generation, Unsplash for images, and python-pptx for PowerPoint export. Built with modern Python async patterns and PostgreSQL database.

---

## 📸 Скриншоты/Демонстрация

- Swagger UI: `http://localhost:8000/docs`
- Пример PPTX (скриншоты):
  - ![Image Left](docs/screenshots/pptx_image_left.png)
  - ![Image Right](docs/screenshots/pptx_image_right.png)
  - ![Split Content](docs/screenshots/pptx_split.png)

---

## ✨ Основные функции

- **🤖 AI-генерация контента** через OpenRouter (OpenAI совместимый API)
- **🖼️ Интеграция с Unsplash** для поиска изображений
- **💾 Экспорт в PPTX** с корректной стилизацией темной/светлой темы
- **📐 6 макетов слайдов**: image_left, image_right, image_top, split_content, grid_layout, text_only
- **🎨 Темы**: minimalist, professional, gradient, dark, creative
- **🔄 Переупорядочивание слайдов** и CRUD операции
- **⚡ Async архитектура** и CORS

---

## 🛠️ Технологический стек

- FastAPI, Uvicorn
- SQLAlchemy 2.0 (async), PostgreSQL, AsyncPG, Alembic
- OpenAI SDK (через OpenRouter), HTTPX, aiohttp
- python-pptx, Pillow, aiofiles
- Pydantic v2, python-dotenv

---

## 🚀 Установка и запуск

### Требования
- Python 3.11+
- PostgreSQL 14+

### Шаги
1. Создайте виртуальное окружение и установите зависимости:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Настройте `.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/presentations_db
   OPENROUTER_API_KEY=your_openrouter_api_key
   UNSPLASH_ACCESS_KEY=your_unsplash_access_key
   UNSPLASH_APPLICATION_ID=your_unsplash_app_id
   UNSPLASH_SECRET_KEY=your_unsplash_secret_key
   BACKEND_CORS_ORIGINS=http://localhost:5173
   ```
3. Инициализируйте БД и миграции:
   ```bash
   alembic upgrade head
   ```
4. Запустите сервер:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

---

## 🔌 Основные эндпоинты
- `POST /api/presentations` — создать презентацию
- `GET /api/presentations` — список презентаций
- `GET /api/presentations/{id}` — презентация по ID
- `PATCH /api/slides/{id}` — обновить слайд
- `PATCH /api/presentations/{id}/reorder` — переупорядочить слайды
- `DELETE /api/presentations/{id}` — удалить
- `GET /api/presentations/{id}/download/pptx` — скачать PPTX
- `GET /api/proxy/image` — прокси изображений Unsplash

---

## 📁 Структура проекта
```
backend/
├── services/
│   ├── ai_service.py
│   ├── image_service.py
│   ├── presentation_service.py
│   └── pptx_service.py
├── alembic/
├── main.py
├── models.py
├── database.py
├── requirements.txt
└── README.md
```

---

## 📝 Лицензия

MIT
