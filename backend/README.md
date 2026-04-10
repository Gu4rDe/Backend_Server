# Backend — FastAPI Server

FastAPI сервер для системы распознавания лиц.

## Требования

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)

## Установка

```bash
cd backend
uv sync
```

## Запуск (разработка)

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Сервер доступен по адресу `http://localhost:8000`.

## Структура

```
backend/
├── app/
│   ├── main.py           # Точка входа FastAPI
│   ├── database.py      # SQLAlchemy настройки
│   ├── models.py        # SQLAlchemy модели (Admin, Employee)
│   ├── schemas.py       # Pydantic схемы
│   ├── auth.py         # JWT аутентификация
│   ├── deps.py         # Зависимости (get_current_admin)
│   └── services/       # Бизнес-логика
│       ├── face_service.py    # Распознавание лиц
│       └── invite_service.py  # Система приглашений
├── models/              # Модели распознавания (arcface.onnx)
├── data/                # SQLite база данных
└── .env                 # Конфигурация
```

## Конфигурация

Создайте `.env` в директории `backend/`:

```env
SECRET_KEY=ваш_секретный_ключ_минимум_32_символа
DATABASE_URL=sqlite:///./data/faces.db
MODEL_DIR=models
```

Полный список переменных см. в [](../README.md#конфигурация).

## Модели распознавания

Для работы распознавания лиц требуется скачать ArcFace ONNX модель.

Подробнее: [MODELS.md](MODELS.md)

## Развёртывание на сервер

Для продакшен развёртывания см. [BACKEND_SETUP.md](BACKEND_SETUP.md):
- Настройка systemd service
- Nginx reverse proxy
- SSL Let's Encrypt
- PostgreSQL миграция

## Связанные документы

- [](../README.md) — Общая документация проекта
- [MODELS.md](MODELS.md) — Модели распознавания
- [BACKEND_SETUP.md](BACKEND_SETUP.md) — Развёртывание на сервере