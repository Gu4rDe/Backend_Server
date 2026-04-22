# Backend — FastAPI Server

FastAPI сервер для системы распознавания лиц с расширенным логированием и автоматической инициализацией.

## Требования

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose (опционально)

## Установка

```bash
cd backend
uv sync
```

## Запуск (разработка)

```bash
uv run uvicorn app.main:app --reload --port 8000
```

## Первый запуск

При первом запуске автоматически:

1. Создаётся `.env` файл с:
   - Сгенерированным `SECRET_KEY` для JWT токенов
   - Сгенерированным `INITIAL_INVITE_CODE` для регистрации первого админа

2. Инициализируется база данных
3. Создаются настройки приложения по умолчанию

### Логирование при запуске

При первом запуске вы увидите в терминале:

```
INFO: Checking for .env file...
INFO: .env file not found, creating new one...
INFO: Generated SECRET_KEY
INFO: Generated INITIAL_INVITE_CODE: aB3xK9mP2qR7sT1v
INFO: Created .env file at /path/to/backend/.env
INFO: Initializing database...
INFO: Database initialized successfully
INFO: Creating default application settings...
INFO: Default settings created
INFO: Face Recognition API starting up...
```

> **Важно:** Скопируйте `INITIAL_INVITE_CODE` из логов — он нужен для регистрации первого администратора!

При повторных запусках:

```
INFO: .env file already exists, skipping creation
INFO: Initializing database...
INFO: Database initialized successfully
INFO: Face Recognition API starting up...
```

Сервер доступен по адресу `http://localhost:8000`.

## Docker

### Быстрый запуск

```bash
cd backend
docker compose up -d
```

API будет доступен по адресу `http://localhost:8000`.

### Сборка образа

```bash
docker build -t face-recognition-api .
```

### Запуск с docker-compose

```bash
docker compose up -d
```

### Просмотр логов

```bash
docker compose logs -f api
```

### Остановка

```bash
docker compose down
```

### Особенности Docker конфигурации

- **Multi-stage build** — уменьшает размер образа за счёт разделения сборки и запуска
- **Healthcheck** — автоматическая проверка состояния контейнера через `/health`
- **Volumes** — данные (`data/`) и модели (`models/`) сохраняются между перезапусками
- **Non-root user** — контейнер запускается от пользователя `appuser` для безопасности
- **Auto-download модели** — ArcFace модель загружается автоматически при первом запуске
- **Log rotation** — логи ограничены 10MB на файл, максимум 3 файла

### Docker Compose конфигурация

```yaml
services:
  api:
    build: .
    container_name: face-recognition-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - face-data:/app/data
      - face-models:/app/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Структура

```
backend/
├── app/
│   ├── main.py           # Точка входа FastAPI, lifespan, middleware
│   ├── database.py       # SQLAlchemy настройки, инициализация БД
│   ├── models.py         # SQLAlchemy модели (Admin, Employee, AppSettings)
│   ├── schemas.py        # Pydantic схемы валидации
│   ├── auth.py           # JWT аутентификация
│   ├── deps.py           # Зависимости (get_current_admin)
│   └── routers/          # API маршруты
│       ├── admins.py     # Регистрация и вход админов
│       ├── employees.py  # CRUD операции с сотрудниками
│       ├── faces.py      # Распознавание лиц
│       └── settings.py   # Настройки приложения
│   └── services/         # Бизнес-логика
│       ├── face_service.py    # Распознавание лиц
│       └── invite_service.py  # Система приглашений
├── alembic/              # Миграции базы данных
├── models/               # Модели распознавания (arcface.onnx)
├── data/                 # SQLite база данных
├── Dockerfile            # Multi-stage Docker конфигурация
├── docker-compose.yml    # Docker Compose для удобства запуска
├── entrypoint.sh         # Скрипт запуска Docker
├── pyproject.toml        # Зависимости проекта
└── .env.example          # Шаблон переменных окружения
```

## Конфигурация

При первом запуске `.env` создаётся автоматически с настройками по умолчанию.

### Переменные окружения

| Переменная            | Описание                           | По умолчанию                |
| --------------------- | ---------------------------------- | --------------------------- |
| `SECRET_KEY`          | Секретный ключ для JWT токенов     | auto-generated              |
| `DATABASE_URL`        | URL базы данных                    | `sqlite:///./data/faces.db` |
| `MODEL_DIR`           | Папка с моделями распознавания лиц | `models`                    |
| `INITIAL_INVITE_CODE` | Код для регистрации админов        | auto-generated              |
| `CORS_ORIGINS`        | Разрешённые CORS origins           | `*`                         |

## Модели распознавания

Для работы распознавания лиц требуется скачать ArcFace ONNX модель.

При запуске через Docker модель загружается автоматически.

Подробнее: [MODELS.md](backend/MODELS.md)

## Развёртывание на сервер

Для продакшен развёртывания см. [BACKEND_SETUP.md](backend/BACKEND_SETUP.md):
- Настройка systemd service
- Nginx reverse proxy
- SSL Let's Encrypt
- PostgreSQL миграция

## API Документация

После запуска документация доступна по адресам:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Связанные документы
- [MODELS.md](backend/MODELS.md) — Модели распознавания
- [BACKEND_SETUP.md](backend/BACKEND_SETUP.md) — Развёртывание на сервере
