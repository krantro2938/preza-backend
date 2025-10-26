# AI Presentation Builder

Минималистичный генератор презентаций с помощью ИИ, созданный как клон Presenton.

- 🤖 **AI-генерация** через OpenRouter
- 🖼️ **Подбор изображений** из Unsplash
- 🇷🇺 **Полностью русский интерфейс**
- 📱 **Минималистичный дизайн**
- 🏠 **Локальное хранение** пользовательских презентаций
- 👀 **Публичный доступ** ко всем презентациям
- 🚫 **Без регистрации** и потоковой передачи
- 🎨 **Красивые слайд-макеты** вдохновленные Presenton
- 📥 **Экспорт в PPTX** с изображениями и стилизацией

## Технологический стек

### Backend

- **FastAPI** - веб-фреймворк
- **PostgreSQL** - база данных
- **OpenRouter** - ИИ провайдер
- **Unsplash** - хранилище изображений

### Frontend

- **Vite + React** - сборка
- **Tailwind CSS** - стилизация
- **React Router** - маршрутизация
- **Axios** - HTTP клиент

## Установка и запуск

### Требования

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Backend

1. Создайте виртуальное окружение:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
source venv\\Scripts\\activate  # Windows
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:

```bash
cp .env.example .env
# Отредактируйте .env файл с вашими API ключами
```

4. Создайте базу данных PostgreSQL:

```sql
CREATE DATABASE ai_presentations;
```

5. Запустите сервер:

```bash
python run.py
```

Backend будет доступен на http://localhost:8000

### Frontend

1. Установите зависимости:

```bash
cd frontend
npm install
```

2. Запустите сервер:

```bash
npm run dev
```

Frontend будет доступен на http://localhost:5173

### База данных

```bash
docker run --name postgres-container -e POSTGRES_USER=root -e POSTGRES_PASSWORD=secret -p 5432:5432 -d postgres


docker exec -it postgres-container psql -U root -d postgres
docker exec -it postgres-container psql
```

## Переменные окружения

### Backend (.env)

```
DATABASE_URL=postgresql://user:password@localhost:5432/ai_presentations
OPENROUTER_API_KEY=your_openrouter_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
```

## API Документация

После запуска backend, документация API доступна по адресу:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Основные эндпоинты

- `POST /api/presentations` - создание презентации
- `GET /api/presentations` - получение всех презентаций
- `GET /api/presentations/{id}` - получение презентации по ID
- `DELETE /api/presentations/{id}` - удаление презентации
- `GET /api/presentations/{id}/download/pptx` - скачивание презентации в PPTX

## Использование

1. Откройте приложение в браузере
2. Введите тему презентации
3. Выберите количество слайдов и стиль
4. Нажмите "Создать презентацию"
5. Дождитесь генерации и наслаждайтесь результатом!

## Особенности архитектуры

- **Без аутентификации**: Все презентации публичные
- **Локальное сохранение**: Трекинг пользовательских презентаций по ID
- **Минимализм**: Чистый и простой интерфейс
- **Производительность**: Оптимизированные запросы к БД и API

## Лицензия

MIT License