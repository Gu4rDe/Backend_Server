# Backend — FastAPI Server

FastAPI сервер для системы распознавания лиц.

## Требования

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)

## Установка

```bash
uv sync
```

## Запуск

```bash
uv run uvicorn app.main:app --reload --port 8000
```

## API

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/admins/register` | Регистрация |
| POST | `/api/v1/admins/login` | Вход |
| POST | `/api/v1/employees/register` | Добавить сотрудника |
| GET | `/api/v1/employees` | Список сотрудников |
| DELETE | `/api/v1/employees/{id}` | Удалить сотрудника |
| POST | `/api/v1/faces/recognize` | Распознать лицо |
| GET | `/health` | Проверка состояния |

## Структура

```
backend/
├── app/
│   ├── main.py        # Приложение
│   ├── models.py      # SQLAlchemy модели
│   ├── schemas.py     # Pydantic схемы
│   └── services/      # Бизнес-логика
└── data/              # База данных
```
