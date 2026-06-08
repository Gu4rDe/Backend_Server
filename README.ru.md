# Сервер распознавания лиц

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?logo=python)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Version](https://img.shields.io/badge/version-6.0.0-orange.svg)]()

[English](README.md) | Русский

REST API сервер для системы распознавания лиц **Miit_FaceDetect**. Построен на **FastAPI** и **SQLAlchemy**, обеспечивает аутентификацию администраторов, управление сотрудниками, распознавание лиц через insightface buffalo_l и настройки приложения.

## Возможности

- **Аутентификация администраторов** — вход, регистрация по пригласительным кодам, сброс пароля по email, JWT-токены
- **Управление сотрудниками** — CRUD-операции, пагинация, поиск, статистика
- **Распознавание лиц** — insightface buffalo_l (SCRFD-10GF + ArcFace R50, 512-мерные эмбеддинги float32), CLAHE-препроцессинг, выравнивание по 5 ключевым точкам, регистрация ровно по 3 фото (усреднение эмбеддингов)
- **Шифрование эмбеддингов** — AES-256-GCM шифрование при хранении с обратной совместимостью
- **Сброс пароля по email** — токены с ограничением срока действия (1 час), одноразовые, кулдаун 5 минут между письмами
- **Настройки приложения** — порог совпадения, параметры камеры, уведомления
- **Ограничение запросов** — защита эндпоинтов через slowapi
- **Автоинициализация** — `.env`, база данных и настройки по умолчанию создаются при первом запуске
- **Docker** — многоэтапная сборка, healthcheck, автоматическая загрузка моделей insightface
- **Тесты** — pytest — 54 теста с in-memory SQLite

## Технологии

| Слой | Технология | Версия |
|------|------------|---------|
| Фреймворк | FastAPI | 0.110.0 |
| Язык | Python | 3.10+ (<3.13) |
| Менеджер пакетов | uv | — |
| ORM | SQLAlchemy | 2.0.23 |
| Миграции | Alembic | 1.13.1 |
| БД | SQLite | встроенная |
| Аутентификация | python-jose + bcrypt | 3.3.0 / 4.0.1 |
| Шифрование | cryptography | 42.0.0 |
| Валидация | Pydantic | 2.10.0 |
| Детекция лиц | insightface SCRFD-10GF | 0.7.3 |
| Распознавание лиц | insightface ArcFace R50 | buffalo_l |
| Инференс | onnxruntime | 1.23.2 |
| Препроцессинг | OpenCV (headless) | 4.8.0.76 |
| Email | fastapi-mail | 1.4.0+ |
| Ограничение запросов | slowapi | 0.1.9 |
| Сервер | Uvicorn | 0.24.0 |

## Архитектура

```
Клиент ──▶ Роутеры ──▶ Сервисы ──▶ База данных
                            │
                    ┌───────▼───────┐
                    │  insightface   │
                    │  (SCRFD +      │
                    │  ArcFace R50)  │
                    └───────────────┘
```

**Ключевые решения:**
- **Синглтон** — один экземпляр `FaceRecognitionService` через `app.state`
- **CLAHE** — применяется ко всему изображению перед детекцией для улучшения видимости при плохом свете
- **float32 эмбеддинги** — 2048 байт каждый, зашифрованы при хранении (AES-256-GCM), с автоматической конвертацией устаревших float64
- **Динамический порог** — берётся из `AppSettings.match_threshold`, а не хардкодится
- **Сброс пароля по email** — токены хранятся в БД, одноразовые, срок действия 1 час, кулдаун 5 минут между письмами

## Установка

1. **Клонировать репозиторий**

```bash
git clone <url-репозитория>
cd <имя-репозитория>/backend
```

2. **Установить зависимости**

```bash
uv sync
uv sync --group dev   # для тестирования
```

3. **Модели insightface** скачиваются автоматически при первом запуске (~32 МБ).

## Запуск

### Режим разработки

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Документация API: http://localhost:8000/docs (Swagger), http://localhost:8000/redoc

### Первый запуск

При первом запуске система автоматически:
1. Создаёт `.env` со сгенерированными `SECRET_KEY`, `ENCRYPTION_KEY` и `INITIAL_INVITE_CODE`
2. Инициализирует базу данных SQLite
3. Загружает модели `buffalo_l` при первом запросе распознавания
4. Создаёт настройки приложения по умолчанию

> **Важно:** Скопируйте `INITIAL_INVITE_CODE` из логов — он нужен для регистрации первого администратора!

### Docker

```bash
cd backend
docker compose build
docker compose up -d
```

Модели insightface скачиваются автоматически при первом запуске контейнера.

### Тесты

```bash
uv run pytest tests/ -v
```

### Миграции базы данных

```bash
uv run alembic upgrade head                              # Применить миграции
uv run alembic revision --autogenerate -m "описание"     # Создать миграцию
uv run alembic downgrade -1                              # Откатить
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SECRET_KEY` | Секретный ключ JWT | автогенерация |
| `ENCRYPTION_KEY` | Ключ AES-256-GCM для шифрования эмбеддингов (base64) | автогенерация |
| `DATABASE_URL` | URL подключения к БД | `sqlite:///./data/faces.db` |
| `INITIAL_INVITE_CODE` | Код регистрации первого админа | автогенерация |
| `SMTP_HOST` | SMTP-сервер для отправки писем сброса пароля | `smtp.yandex.ru` |
| `SMTP_PORT` | Порт SMTP-сервера | `587` |
| `SMTP_USER` | Логин SMTP (полный email) | — |
| `SMTP_PASSWORD` | Пароль SMTP (или пароль приложения) | — |
| `SMTP_FROM` | Email отправителя | `noreply@example.com` |
| `FRONTEND_URL` | URL фронтенда для ссылок сброса пароля | `http://localhost:3000` |
| `CORS_ORIGINS` | Разрешённые источники CORS | `*` |

> **Примечание:** Если `SMTP_HOST` или `SMTP_USER` пустые, письма сброса пароля отправляться не будут. Эндпоинт `/forgot-password` всё равно вернёт 200, но залогирует ошибку.

> **Внимание:** При смене `ENCRYPTION_KEY` существующие эмбеддинги станут недоступны. Храните ключ в безопасности и делайте резервные копии.

### Пайплайн распознавания лиц

| Шаг | Компонент | Детали |
|-----|-----------|--------|
| 1. Препроцессинг | CLAHE | BGR→LAB, clipLimit=2.0, tileGridSize=(8,8) |
| 2. Детекция | SCRFD-10GF | 5 ключевых точек, порог уверенности |
| 3. Выравнивание | norm_crop | similarity transform по 5 точкам → 112×112 |
| 4. Распознавание | ArcFace R50 | 512-мерный эмбеддинг float32 |
| 5. Сравнение | Косинусное сходство | матрично-векторное умножение, порог из настроек |

### Шифрование эмбеддингов

Эмбеддинги шифруются алгоритмом **AES-256-GCM** перед сохранением в базу данных.

| Свойство | Значение |
|----------|----------|
| Алгоритм | AES-256-GCM (аутентифицированное шифрование) |
| Ключ | 256 бит, хранится как base64 в переменной `ENCRYPTION_KEY` |
| Nonce | 12 случайных байт при каждом шифровании (разный шифротекст каждый раз) |
| Формат | `[0x01 версия][12B nonce][шифротекст + 16B GCM тег]` |
| Накладные расходы | 29 байт на эмбеддинг (1 + 12 + 16) |
| Обратная совместимость | Незашифрованные float32/float64 эмбеддинги определяются по отсутствию префикса `0x01` |

### Формат эмбеддингов

| Свойство | Значение |
|----------|----------|
| Размерность | 512 |
| Тип данных | float32 |
| Размер (без шифрования) | 2048 байт на сотрудника |
| Размер (с шифрованием) | 2077 байт на сотрудника (2048 + 29 накладных расходов) |
| Хранение | SQLite BLOB (зашифровано) |
| Обратная совместимость | Автоопределение незашифрованных float32/float64 |

## API

**Базовый URL:** `http://localhost:8000`

### Аутентификация

| Метод | Эндпоинт | Авторизация | Тело | Ответ |
|-------|----------|-------------|------|-------|
| POST | `/api/v1/admins/register` | — | `{username, email, password, invite_code}` | `{id, username, email, created_at}` |
| POST | `/api/v1/admins/login` | — | `{username, password}` | `{access_token, token_type}` |
| GET | `/api/v1/admins/me` | Да | — | `{id, username, email, created_at}` |
| POST | `/api/v1/admins/forgot-password` | — | `{username}` | `{message}` (200, без перечисления имён) |
| POST | `/api/v1/admins/reset-password` | — | `{token, new_password}` | `{message}` |
| POST | `/api/v1/admin/invites` | Да | `{expires_hours}` | `{id, code, ...}` |
| GET | `/api/v1/admin/invites` | Да | — | `{codes: [{InviteCodeResponse}], total: number}` |
| DELETE | `/api/v1/admin/invites/{id}` | Да | — | `200 OK` |

### Сотрудники

| Метод | Эндпоинт | Авторизация | Тело | Ответ |
|-------|----------|-------------|------|-------|
| POST | `/api/v1/employees/register` | Да | Multipart (ровно 3 фото + форма) | `{EmployeeResponse}` |
| POST | `/api/v1/employees/{id}/re-embed` | Да | Multipart (ровно 3 фото) | `{EmployeeResponse}` |
| GET | `/api/v1/employees` | Да | Query: `skip`, `limit` | `[{EmployeeResponse}]` |
| GET | `/api/v1/employees/search` | Да | Query: `q` | `[{EmployeeResponse}]` |
| GET | `/api/v1/employees/stats` | Да | — | `{total, active, inactive}` |
| PUT | `/api/v1/employees/{id}` | Да | `{EmployeeUpdate}` | `{EmployeeResponse}` |
| DELETE | `/api/v1/employees/{id}` | Да | — | `200 OK` |

### Распознавание лиц

| Метод | Эндпоинт | Авторизация | Тело | Ответ |
|-------|----------|-------------|------|-------|
| POST | `/api/v1/faces/recognize` | Да | Multipart (изображение) | `{faces_detected, results}` |

### Настройки

| Метод | Эндпоинт | Авторизация | Тело | Ответ |
|-------|----------|-------------|------|-------|
| GET | `/api/v1/settings` | Да | — | `{AppSettings}` |
| PUT | `/api/v1/settings` | Да | `{AppSettingsUpdate}` | `{AppSettings}` |
| POST | `/api/v1/settings/backup` | Да | — | `{message, backup_path}` |

### Health Check

| Метод | Эндпоинт | Авторизация | Ответ |
|-------|----------|-------------|-------|
| GET | `/health` | — | `{status: "healthy", service, version}` |
| GET | `/` | — | `{message}` |

## Тестирование

```bash
uv run pytest tests/ -v
```

- In-memory SQLite с `StaticPool` — файловая БД не нужна
- Модели insightface для тестов не требуются
- `conftest.py` устанавливает все переменные окружения до импорта `app.*`
- Всего 54 теста

## Вклад в проект

1. Форкните репозиторий
2. Создайте ветку функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## Лицензия

Проект распространяется под лицензией MIT. См. [LICENSE](LICENSE) для подробностей.