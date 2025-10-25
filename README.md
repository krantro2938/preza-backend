## 📦 Обзор

Бэкенд реализован на **FastAPI** и взаимодействует с **PostgreSQL** для хранения метаданных презентаций. Все презентации публичны, аутентификация не требуется. Сервис интегрируется с внешними API: **OpenRouter** (для генерации текста) и **Unsplash** (для изображений).

## ⚙️ Технологический стек

|Компонент|Технология
|-|-
|Веб-фреймворк|FastAPI
|Язык|Python 3.12
|База данных|PostgreSQL 15
|ORM / DB-доступ|SQLAlchemy
|Внешние API|OpenRouter, Unsplash
|Контейнеризация|Docker
|Документация API|Swagger UI / ReDoc

## Установка и запуск

### Backend

1. Создайте виртуальное окружение:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\\Scripts\\activate  # Windows
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

## DATABASE

```bash
docker run --name postgres-container -e POSTGRES_USER=root -e POSTGRES_PASSWORD=secret -p 5432:5432 -d postgres


docker exec -it postgres-container psql -U root -d postgres
docker exec -it postgres-container psql
```

## API Документация

После запуска backend, документация API доступна по адресу:
- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc

### Основные эндпоинты
|Метод|Путь|Описание|
|-|-|-|
|POST|`/api/presentations`|Создание презентации
|GET|`/api/presentations`|Получение всех презентаций  
|GET|`/api/presentations/{id}`|Получение презентации по ID
|DELETE|`/api/presentations/{id}`|Удаление презентации
|GET|`/api/presentations/{id}/download/pptx`|Скачивание презентации в PPTX

## 🐳 Docker-развертывание

Проект поддерживает запуск через Docker Compose.

### Состав сервисов

|Сервис|Назначение|
|-|-|
|`postgres`|PostgreSQL 15 с преднастроенной БД
|`fastapi`|FastAPI-приложение
|`pgadmin`|Веб-интерфейс для администрирования PostgreSQL

## Переменные окружения

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/ai_presentations
OPENROUTER_API_KEY=your_openrouter_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
```
