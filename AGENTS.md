# AGENTS.md

## Обзор проекта

Бэкенд распознавания лиц — REST API на FastAPI + SQLAlchemy с распознаванием лиц (insightface buffalo_l: SCRFD + ArcFace R50), шифрованием эмбеддингов AES-256-GCM, JWT-авторизацией и хранением в SQLite.

## Рабочая директория

**Все команды выполняются из `backend/`, а не из корня репозитория.**

```
cd backend
uv run uvicorn app.main:app --reload --port 8000
uv run pytest tests/ -v
uv run alembic upgrade head
```

## Менеджер пакетов

`uv` — не использовать pip напрямую.

```bash
uv sync                    # установить runtime-зависимости
uv sync --group dev        # установить + dev-зависимости (pytest, httpx)
```

## Окружение и секреты

- `.env` **создаётся автоматически** при первом запуске — никогда не создавайте его вручную
- `SECRET_KEY`, `ENCRYPTION_KEY`, `INITIAL_INVITE_CODE`, `RESET_INVITE_CODE` генерируются и логируются при старте
- **Смена `ENCRYPTION_KEY` делает все хранимые эмбеддинги нечитаемыми** — пути миграции нет
- Тестовые фикстуры в `tests/conftest.py` устанавливают все env-переменные до импорта `app.main`

## Структура проекта

```
backend/
  app/
    main.py              # FastAPI-приложение, lifespan, middleware
    database.py          # SQLAlchemy-сессия, инициализация БД, авто-создание .env
    models.py            # SQLAlchemy-модели (Admin, Employee, AppSettings, AdminInviteCode)
    schemas.py           # Pydantic-схемы запросов/ответов
    auth.py              # JWT (HS256, срок 24ч) + bcrypt
    deps.py               # FastAPI-зависимости (get_face_service-синглтон, get_current_admin)
    utils.py             # Декодирование изображений, sanitize строк
    routers/             # HTTP-эндпоинты (admins, employees, faces, settings)
    services/
      face_service.py    # FaceRecognitionService — синглтон через app.state
      crypto.py          # AES-256-GCM шифрование/расшифровка эмбеддингов
      embedding.py       # Сериализация эмбеддингов (float32 → зашифрованный blob)
      invite_service.py  # CRUD для пригласительных кодов
  alembic/               # Миграции БД
  tests/                 # pytest (in-memory SQLite, модели не нужны)
  data/                  # SQLite-база (в .gitignore)
```

## Архитектура: паттерн Singleton

`FaceRecognitionService` создаётся один раз в `lifespan` и хранится в `app.state.face_service`. Зависимость `get_face_service` извлекает его оттуда. Не создавать новые экземпляры.

## Модель распознавания лиц

Единственный провайдер — **insightface buffalo_l** (SCRFD-10GF детекция + ArcFace R50 эмбеддинги). Резервного ONNX-провайдера нет. Если insightface недоступен при инициализации, сервис не запустится.

## Формат эмбеддингов

- 512-мерные float32-эмбеддинги, шифруются AES-256-GCM при хранении
- Формат в БД: `[0x01 версия][12B nonce][шифротекст + 16B GCM-тег]`
- Устаревшие нешифрованные float32 (2048 байт) и float64 (4096 байт) определяются по отсутствию префикса `0x01`
- Обратная совместимость — в `services/embedding.py::deserialize_embedding()`

## Тестирование

```bash
uv run pytest tests/ -v
```

- In-memory SQLite с `StaticPool` — файловая БД не нужна
- insightface-модели для тестов не требуются
- `conftest.py` устанавливает env-переменные до любого импорта `app.*`
- Тестовый `ENCRYPTION_KEY`: `n5RB92P5EAO1cpfUkhhKBGS1LKMt7gmwMobJPU7-pTI=`

## Миграции БД

```bash
uv run alembic upgrade head                       # применить миграции
uv run alembic revision --autogenerate -m "desc"  # создать миграцию
uv run alembic downgrade -1                       # откатить
```

## Ключевые ограничения

- Python `>=3.10,<3.13`
- Регистрация лица сотрудника требует ровно 3 фото; эмбеддинги усредняются (mean + L2-norm)
- Rate limiting: регистрация (5/мин), логин (10/мин) через slowapi
- JWT-токены используют `id` администратора как `"sub"` (строка)
- Префикс API: `/api/v1/` для всех эндпоинтов, `/health` и `/` — без авторизации

## Линтер/форматтер/тайпчекер не настроены

В `pyproject.toml` нет ruff, black, mypy и подобных инструментов. CI-конфигураций нет. Перед добавлением — уточните у пользователя.

## Docker

```bash
cd backend
docker compose build && docker compose up -d
```

`entrypoint.sh` автоматически скачивает модели insightface `buffalo_l` (~32 МБ) и генерирует `.env` с секретами.