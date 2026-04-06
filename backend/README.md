# Face Recognition System

Система распознавания лиц с веб-интерфейсом администратора и десктопным приложением.

## Архитектура

```
FrontendApps (Desktop GUI - CustomTkinter)
  |
  |  HTTP requests
  v
BackendApps (FastAPI на порту 8000)
  |
  |  SQLAlchemy ORM
  v
SQLite Database (data/faces.db)
  - admins    — администраторы (аутентификация)
  - employees — сотрудники (распознавание)
```

## Требования

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) — менеджер пакетов
- Предобученные модели (см. [MODELS.md](MODELS.md))
  - ArcFace ONNX (~130 MB) — извлечение эмбеддингов лиц
  - MediaPipe — детекция лиц (устанавливается через pip)

## Установка и запуск

### Из корня проекта (рекомендуется)

```bash
# Установка зависимостей
uv sync --directory BackendApps
uv sync --directory FrontendApps

# Запуск бэкенда
uv run --directory BackendApps uvicorn app.main:app --reload --port 8000

# Запуск интерфейса (в другом терминале)
uv run --directory FrontendApps python main.py
```

### Из поддиректории

```bash
cd BackendApps
uv sync
uv run uvicorn app.main:app --reload --port 8000

cd FrontendApps
uv sync
uv run python main.py
```

### Через скрипты (Windows)

```cmd
run-backend.bat
run-frontend.bat
```

## Переменные окружения

Скопируйте `.env.example` в `.env` и настройте:

```bash
DATABASE_URL=sqlite:///./data/faces.db
MODEL_DIR=models
SECRET_KEY=<ваш-секретный-ключ>
CORS_ORIGINS=*
```

> **Важно:** `SECRET_KEY` обязателен. Сгенерируйте его командой:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

## API

### Администраторы

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/admins/register` | Регистрация администратора |
| POST | `/api/v1/admins/login` | Вход администратора |
| GET | `/api/v1/admins/me` | Информация о текущем админе |

### Сотрудники

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/employees/register` | Добавить сотрудника (фото + ФИО+должность) |
| GET | `/api/v1/employees` | Список всех сотрудников |
| DELETE | `/api/v1/employees/{id}` | Удалить сотрудника |

### Распознавание

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/faces/recognize` | Распознавание лица на фото |
| GET | `/health` | Проверка состояния |

## Модели распознавания

### Детекция лиц
Используется **MediaPipe Face Detection** — лёгкая и быстрая модель, устанавливается автоматически через pip.

### Извлечение эмбеддингов
Используется **ArcFace ResNet-100** в формате ONNX:
- Вход: обрезанное изображение лица 112x112
- Выход: 512-мерный нормализованный вектор
- Точность: 90%+ при верификации лиц
- Порог совпадения (косинусное сходство): 0.4

Если файл `arcface.onnx` отсутствует, система автоматически переключается на fallback-режим (гистограммы) с пониженной точностью.

Подробнее: [MODELS.md](MODELS.md)

## Модели базы данных

### Admin (admins)

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| username | String(50) | Уникальное имя |
| email | String(100) | Уникальный email |
| password_hash | String(255) | Хеш пароля |
| created_at | DateTime | Дата создания |

### Employee (employees)

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| username | String(150) | ФИО + Должность |
| embedding | LargeBinary | Векторное представление лица |

## Структура проекта

```
BackendApps/
├── app/
│   ├── main.py              # FastAPI приложение + маршруты
│   ├── models.py            # SQLAlchemy модели (Admin, Employee)
│   ├── database.py          # Конфигурация БД и сессии
│   ├── schemas.py           # Pydantic схемы запросов/ответов
│   ├── auth.py              # JWT аутентификация
│   └── services/
│       ├── __init__.py
│       └── face_service.py  # Сервис распознавания лиц
├── data/                    # База данных SQLite
├── models/                  # Предобученные модели
├── .env.example
├── MODELS.md                # Инструкции по моделям
├── BACKEND_SETUP.md         # Инструкция по развёртыванию
├── pyproject.toml
└── README.md
```

## Локализация

Интерфейс поддерживает русский и английский языки. Переключение через окно настроек (кнопка ⚙ в главном окне). Язык сохраняется в `lang_config.json`.
