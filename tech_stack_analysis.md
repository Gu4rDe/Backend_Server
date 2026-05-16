# Анализ технологических стеков - Miit_FaceDetect

---

## 📊 Содержание
1. [Проект 1: Backend Server (FastAPI)](#проект-1-backend-server-fastapi)
2. [Проект 2: Face Recognition System (Kotlin Compose)](#проект-2-face-recognition-system-kotlin-compose)
3. [Требования к железу](#требования-к-железу)
4. [Сравнительная таблица](#сравнительная-таблица)

---

## Проект 1: Backend Server (FastAPI)

**Репозиторий:** https://github.com/Gu4rDe/Backend_Server

**Назначение:** REST API сервер для системы распознавания лиц с поддержкой JWT аутентификации, управления сотрудниками и расширенным логированием.

### 🛠️ Основные технологии

#### **Язык программирования**
- **Python** >= 3.10
  - Выбран за быстроту разработки и наличие мощных библиотек для ML/CV
  - Поддержка современных типов (Type Hints) для лучшей IDE поддержки
  - Асинхронное программирование через asyncio

#### **Backend фреймворк**
- **FastAPI** (версия не указана, последняя ~0.104.1)
  - Асинхронный веб-фреймворк на основе ASGI
  - Автоматическая генерация OpenAPI документации (Swagger UI, ReDoc)
  - Валидация данных через Pydantic
  - Встроенная поддержка JWT токенов
  - Высокая производительность благодаря uvicorn

#### **Сервер приложений**
- **Uvicorn** (версия не указана, последняя ~0.24.0)
  - ASGI веб-сервер на базе asyncio
  - Поддержка автоматической перезагрузки (`--reload`) для разработки
  - Горячая перезагрузка кода (в development режиме)

#### **База данных**
- **SQLite** (по умолчанию)
  - Файловая база данных, не требует отдельного сервера
  - Подходит для разработки и небольших систем
  - **Миграция на PostgreSQL** рекомендуется для production

- **SQLAlchemy** (версия не указана, последняя ~2.0.23)
  - ORM для взаимодействия с БД
  - Поддержка миграций через Alembic
  - Cross-database compatible (SQLite, PostgreSQL, MySQL)

#### **Миграции базы данных**
- **Alembic** (версия не указана, последняя ~1.12.1)
  - Система управления версиями схемы БД
  - Автоматическое создание скриптов миграции
  - Отслеживание изменений структуры данных

#### **Валидация данных**
- **Pydantic** (версия не указана, последняя ~2.4.2)
  - Валидация и сериализация данных через Python models
  - Проверка типов при runtime
  - Автоматическая генерация JSON схем

#### **Компьютерное зрение и ML**
- **OpenCV** (версия не указана, cv2)
  - Обработка видео с веб-камер
  - Предварительная обработка изображений (resize, normalize)
  - Рисование bounding boxes

- **ONNX Runtime** (версия не указана, последняя ~1.16.0)
  - Кросс-платформенный runtime для нейросетей
  - Высокая производительность
  - Поддержка GPU (опционально)

- **ArcFace ONNX модель**
  - Предобученная модель для распознавания лиц
  - Высокая точность (89.6% на LFW dataset)
  - Легкая (весит ~181MB)
  - Работает без GPU

#### **Управление зависимостями**
- **uv** (versioning package manager)
  - Супер-быстрый package manager, написанный на Rust
  - Замена pip с лучшей производительностью
  - Использует `pyproject.toml` для конфигурации

#### **Контейнеризация**
- **Docker**
  - Multi-stage build для минимизации размера образа
  - Образ содержит всё необходимое для запуска
  - Автоматическая загрузка моделей ArcFace при первом запуске

- **Docker Compose**
  - Оркестрация контейнеров
  - Volume для сохранения данных между перезапусками
  - Healthcheck для мониторинга состояния сервиса

#### **Логирование**
- **Python logging** (встроенный модуль)
  - Подробное логирование при запуске
  - Информация о создании `.env` и инициализации БД
  - Ротация логов (10MB на файл, макс 3 файла)

#### **Аутентификация**
- **JWT (JSON Web Tokens)**
  - Безопасные токены для API аутентификации
  - Token-based authentication вместо session-based
  - SECRET_KEY генерируется автоматически при первом запуске

### 📂 Структура проекта
```
backend/
├── app/
│   ├── main.py              # Точка входа, lifespan, middleware
│   ├── database.py          # SQLAlchemy и инициализация
│   ├── models.py            # Admin, Employee, AppSettings (SQLAlchemy)
│   ├── schemas.py           # Pydantic валидация
│   ├── auth.py              # JWT логика
│   ├── deps.py              # Dependency injection
│   └── routers/             # API endpoints
│       ├── admins.py        # POST /register, POST /login
│       ├── employees.py     # CRUD операции
│       ├── faces.py         # Распознавание (POST /recognize)
│       └── settings.py      # Конфигурация приложения
│   └── services/
│       ├── face_service.py  # Логика распознавания
│       └── invite_service.  # Коды приглашений
├── alembic/                 # Миграции БД
├── models/                  # Предобученные модели (arcface.onnx)
├── data/                    # Файл БД (faces.db)
├── Dockerfile               # Multi-stage Docker
├── docker-compose.yml       # Конфигурация compose
├── pyproject.toml           # Зависимости (через uv)
└── .env                     # Переменные окружения (авто-генерируется)
```

### 🔑 Ключевые особенности
- **Автоматическая инициализация** - при первом запуске создаёт `.env` и инициализирует БД
- **REST API** - полная OpenAPI документация через Swagger UI
- **JWT токены** - безопасная аутентификация
- **Система приглашений** - только админ может создать первого админа через INITIAL_INVITE_CODE
- **Docker ready** - multi-stage build, healthcheck, volumes
- **Cross-platform** - работает на Windows, macOS, Linux

---

## Проект 2: Face Recognition System (Kotlin Compose)

**Репозиторий:** https://github.com/Gu4rDe/Face_Recognition_System

**Назначение:** Desktop приложение для взаимодействия с Backend Server. Управление сотрудниками, распознавание лиц в реальном времени, настройки приложения.

### 🛠️ Основные технологии

#### **Язык программирования**
- **Kotlin** 2.3.20
  - Современный язык для JVM с nullability safety
  - 100% совместимость с Java, но с удобнее синтаксис
  - Поддержка coroutines для асинхронного кода
  - Compile-time null safety

#### **UI фреймворк**
- **Compose Multiplatform** 1.10.3
  - Декларативный UI фреймворк (как React)
  - Поддержка Desktop, Android, iOS, Web (теоретически)
  - Hot reload для быстрой разработки
  - Основан на реактивном подходе

- **Material3** 1.10.0-alpha05
  - Modern Material Design система
  - Светлая/темная тема (динамическая смена)
  - Pre-built компоненты (Button, TextField, etc.)
  - Accessible по умолчанию

#### **Навигация**
- **Voyager** 1.1.0-beta01
  - Навигационная библиотека для Compose
  - Stack-based навигация (как в мобильных приложениях)
  - Screen-centric архитектура
  - Support для back button и history

#### **HTTP клиент**
- **Ktor Client** 3.0.3
  - Асинхронный HTTP клиент
  - Мультиплатформенный (JVM, Native, JS)
  - CIO engine для Desktop (non-blocking I/O)
  - Поддержка multipart uploads

#### **Сериализация**
- **kotlinx-serialization-json** 1.7.3
  - Type-safe JSON сериализация
  - Поддержка custom serializers
  - Zero-reflection подход
  - Конфигурируемо (ignoreUnknownKeys, encodeDefaults, etc.)

#### **Асинхронное программирование**
- **kotlinx-coroutines-swing** 1.10.2
  - Coroutines для Swing (основа Desktop)
  - Non-blocking операции
  - Structured concurrency
  - Main dispatcher для UI обновлений

#### **Lifecycle управление**
- **androidx.lifecycle** 2.10.0
  - ViewModel pattern для сохранения состояния
  - Lifecycle-aware компоненты
  - Автоматическая очистка ресурсов

#### **Логирование**
- **SLF4J** 2.0.16
  - Абстракция над logging фреймворками
  - Логирование API запросов и errors
  - Разные уровни (DEBUG, INFO, WARN, ERROR)

#### **Build система**
- **Gradle** (Kotlin Multiplatform Plugin)
  - Современная build система
  - Kotlin DSL для конфигурации
  - Управление зависимостями
  - Встроенная поддержка тестирования

#### **Тестирование**
- **JUnit** 4.13.2
  - Unit тесты для бизнес-логики
  - Интеграция с Gradle

#### **Горячая перезагрузка**
- **Compose Hot Reload** 1.0.0
  - Мгновенное обновление UI при изменении кода
  - Ускоренная разработка
  - Сохранение состояния приложения

#### **Упаковка приложения**
- **Compose Desktop** packaging
  - MSI installer для Windows
  - DMG для macOS
  - Deb для Linux
  - Встроенная JVM (для standalone дистрибьютива)

### 📂 Структура проекта (Clean Architecture)

```
com.example.kotlinapp
├── main.kt                      # Entry point (Window)
├── App.kt                       # Root composable
├── ServiceLocator.kt            # Singleton DI container
│
├── domain/                      # Business logic (NO external deps)
│   ├── model/                   # Business entities
│   │   ├── Admin.kt            # Admin данные
│   │   ├── Employee.kt         # Сотрудник
│   │   ├── FaceRecognitionResult.kt
│   │   ├── AuthResult.kt
│   │   ├── InviteCode.kt
│   │   └── Settings.kt
│   │
│   └── repository/              # Interfaces (contracts)
│       ├── AuthRepository.kt
│       ├── EmployeeRepository.kt
│       ├── FaceRecognitionRepository.kt
│       ├── InviteCodeRepository.kt
│       └── SettingsRepository.kt
│
├── data/                        # Implementation (depends on domain)
│   ├── local/
│   │   └── LocalSettingsStorage.kt  # java.util.prefs.Preferences
│   │
│   ├── dto/                     # Data Transfer Objects (snake_case)
│   │   ├── AuthDto.kt
│   │   ├── EmployeeDto.kt
│   │   ├── FaceRecognitionDto.kt
│   │   ├── InviteCodeDto.kt
│   │   └── SettingsDto.kt
│   │
│   ├── mapper/                  # DTO <-> Domain conversions
│   │   ├── AuthMappers.kt       # Extension functions
│   │   ├── EmployeeMappers.kt
│   │   ├── FaceRecognitionMappers.kt
│   │   ├── InviteCodeMappers.kt
│   │   └── SettingsMappers.kt
│   │
│   ├── remote/                  # Network layer
│   │   ├── ApiClient.kt         # Ktor HttpClient config
│   │   ├── ApiService.kt        # API методы
│   │   └── ApiException.kt      # Custom exceptions
│   │
│   └── repository/              # Repository implementations
│       ├── AuthRepositoryImpl.kt
│       ├── EmployeeRepositoryImpl.kt
│       ├── FaceRecognitionRepositoryImpl.kt
│       ├── InviteCodeRepositoryImpl.kt
│       └── SettingsRepositoryImpl.kt
│
├── presentation/                # UI state management
│   └── SettingsState.kt         # Settings ViewModel
│
├── screen/                      # Voyager Screens
│   ├── HomeScreen.kt
│   ├── LoginAdminScreen.kt
│   ├── RegisterAdminScreen.kt
│   └── AdminStubScreen.kt
│
├── ui/                          # UI Components
│   ├── buttons/
│   │   └── LoginButton.kt
│   ├── textfields/
│   │   ├── LoginTextField.kt
│   │   └── PasswordTextField.kt
│   ├── icons/
│   │   ├── SettingsIcon.kt
│   │   └── VisibilityIcon.kt
│   ├── settings/
│   │   └── SettingsOverlay.kt
│   └── theme/
│       ├── Color.kt            # Material3 цвета
│       └── Theme.kt            # Light/Dark themes
│
└── util/
    └── ErrorMapper.kt          # Преобразование ошибок в UI messages
```

### 🏗️ Архитектура (Clean Architecture)

```
┌────────────────────────────────┐
│      Presentation Layer         │ ← Screens, Composables, SettingsState
├────────────────────────────────┤
│        Domain Layer             │ ← Models, Repository interfaces
├────────────────────────────────┤
│         Data Layer              │ ← DTOs, ApiClient, Repository impls
└────────────────────────────────┘

Dependency rule: Presentation → Domain ← Data
(Domain не знает о Presentation и Data)
```

### 🔄 Dependency Injection
- **ServiceLocator** (singleton pattern)
  - Централизованное создание и управление зависимостями
  - ApiClient, ApiService, все repositories создаются здесь
  - Единственное место с явными конструкциями

### 🔑 Ключевые особенности
- **Clean Architecture** - строгое разделение слоёв
- **Multi-platform ready** - можно компилировать на разные платформы
- **Hot Reload** - мгновенное обновление UI при изменении кода
- **JWT Bearer auth** - аутентификация через tokens
- **Webcam integration** - захват видео и фотографий
- **Multipart uploads** - загрузка изображений на backend
- **Settings persistence** - сохранение настроек через java.util.prefs
- **Light/Dark theme** - динамическая смена темы
- **Error handling** - user-friendly сообщения об ошибках
- **Desktop packaging** - готовые инсталлеры для всех OS

### 📋 Реализованные фичи
- ✅ Admin Authentication (login, register)
- ✅ Employee Management (CRUD, search, photo)
- ✅ Face Recognition (upload, webcam, results)
- ✅ Settings (API URL, recognition params, theme)
- ✅ Navigation (Voyager screens)
- ✅ Material3 UI

---

## Требования к железу

### **Проект 1: Backend Server (FastAPI)**

#### **Минимальные требования**
| Компонент      | Минимум          | Примечание                          |
| -------------- | ---------------- | ----------------------------------- |
| **CPU**        | 2 ядра @ 2.0 GHz | Intel i5-3rd gen или AMD Ryzen 1000 |
| **RAM**        | 2 GB             | SQLite не требует много памяти      |
| **Диск**       | 2 GB SSD         | Для OS + Python + модели (~200MB)   |
| **Видеокарта** | Не требуется     | CPU inference достаточно            |
| **Сеть**       | 100 Mbps         | Для API запросов                    |

**Оценка:** Может работать на Raspberry Pi 4B (4GB RAM)

#### **требования**
| Компонент      | Рекомендуется                   | Примечание                                     |
| -------------- | ------------------------------- | ---------------------------------------------- |
| **CPU**        | 4+ ядра @ 2.5+ GHz              | Intel i7 или AMD Ryzen 5                       |
| **RAM**        | 8 GB                            | Для обработки нескольких запросов одновременно |
| **Диск**       | 50 GB SSD                       | Для логов, моделей, базы данных                |
| **Видеокарта** | RTX 3060 или выше (необязательно) | CUDA для GPU inference (3-5x ускорение)        |
| **Сеть**       | 100 Mbps                           | Для fast API responses                         |

**Оценка:** Мощная машина обеспечит <100ms processing time

#### **Требования для разработки**
- Python 3.10+
- Docker (рекомендуется)
- ~5 GB диска для всех инструментов

---

### **Проект 2: Face Recognition System (Kotlin Desktop)**

#### **требования**
| Компонент      | Минимум               | Примечание                        |
| -------------- | --------------------- | --------------------------------- |
| **CPU**        | 2 ядра @ 2.0 GHz      | JVM требует немного ресурсов      |
| **RAM**        | 4 GB                  | JVM + Compose требует минимум 4GB |
| **Диск**       | 500 MB                | Для приложения + JVM + libraries  |
| **Видеокарта** | Встроенная            | Для UI отрисовки                  |
| **Дисплей**    | 1024x768              | Минимальное разрешение для UI     |
| **Веб-камера** | USB 2.0 (опционально) | Для face recognition              |

**Оценка:** Может работать на старых ноутбуках, но не комфортно

#### **Рекомендуемые требования**
| Компонент      | Рекомендуется        | Примечание                       |
| -------------- | -------------------- | -------------------------------- |
| **CPU**        | 4+ ядра @ 2.5+ GHz   | Быстрая откомпиляция, smooth UI  |
| **RAM**        | 8+ GB                | Comfortable работа приложения    |
| **Диск**       | 20 GB SSD            | Для IDE, Gradle, build artifacts |
| **Видеокарта** | Discrete (RTX 2060+) | Smooth UI rendering              |
| **Дисплей**    | 1920x1080 @ 60Hz     | Красивый Material3 interface     |
| **Веб-камера** | USB 3.0 @ 30fps      | Smooth video capture             |

**Оценка:** Приятно работается на современных ноутбуках

#### **Требования для разработки**
- JDK 17+ (OpenJDK или Oracle)
- Gradle 8+
- Android Studio / IntelliJ IDEA (опционально)
- ~10 GB диска для всех инструментов

---

### **Объединённые требования (Full Stack)**

#### **Минимальная конфигурация** (один компьютер, разработка)
```
CPU:  4-ядро @ 2.5 GHz
RAM:  8 GB
SSD:  100 GB
GPU:  Integrated
```
**Примеры:** MacBook Air M2, Dell XPS 13, Lenovo ThinkPad X1

#### **Рекомендуемая конфигурация** (production + development)
```
CPU:  8-ядров @ 3.0+ GHz
RAM:  16 GB
SSD:  256 GB
GPU:  RTX 3070 или выше (для GPU inference)
```
**Примеры:** MacBook Pro 14", Dell XPS 15, ASUS ROG

#### **High-performance конфигурация** (enterprise)
```
CPU:  16+ ядер @ 3.5+ GHz (Xeon/Threadripper)
RAM:  32+ GB ECC
SSD:  1 TB NVMe
GPU:  RTX 4090 или A100 (для production inference)
Network: 10 Gbps
```
**Примеры:** Dedicated server, AWS EC2 p3.2xlarge, Azure VM

---

## Сравнительная таблица

| Критерий            | Backend Server                     | Face Recognition System         |
| ------------------- | ---------------------------------- | ------------------------------- |
| **Язык**            | Python 3.10+                       | Kotlin 2.3.20                   |
| **Тип приложения**  | REST API сервер                    | Desktop приложение              |
| **Фреймворк**       | FastAPI + Uvicorn                  | Kotlin Compose Multiplatform    |
| **БД**              | SQLite (+ PostgreSQL для prod)     | Preferences (local)             |
| **Аутентификация**  | JWT tokens                         | JWT Bearer tokens               |
| **Контейнеризация** | Docker + Docker Compose            | Native, упакуется в MSI/DMG/Deb |
| **Асинхронность**   | asyncio (ASGI)                     | Coroutines (Kotlin)             |
| **UI**              | Swagger/ReDoc API docs             | Material3 Desktop UI            |
| **Тестирование**    | Рекомендуется pytest               | JUnit 4                         |
| **Cross-platform**  | Linux/macOS/Windows (через Docker) | Windows/macOS/Linux (native)    |
| **Мин. требования** | 2GB RAM, 2 ядра                    | 4GB RAM, 2 ядра                 |
| **Рекомендуемые**   | 8GB RAM, 4 ядра                    | 8GB RAM, 4 ядра                 |
| **GPU support**     | CUDA (опционально)                 | Нет                             |
| **Документация**    | OpenAPI/Swagger                    | Code + README                   |

---

## 📌 Выводы

### **Backend Server (FastAPI)**
✅ **Плюсы:**
- Простой и быстрый в разработке
- Отличная документация (Swagger UI)
- Асинхронность из коробки
- Docker ready
- Можно масштабировать горизонтально

❌ **Минусы:**
- Требует отдельного запуска сервера
- Python требует виртуального окружения
- GIL может быть узким местом при высокой нагрузке

### **Face Recognition System (Kotlin Compose)**
✅ **Плюсы:**
- Modern UI с Material3
- Type-safe code (Kotlin)
- Hot reload для fast development
- Упаковывается в native приложение
- Clean Architecture

❌ **Минусы:**
- JVM requires 4GB+ RAM
- Первый запуск долгий (JVM загрузка)
- Gradle build может быть медленным

### **Интеграция**
- Оба проекта идеально дополняют друг друга
- Backend предоставляет REST API
- Frontend использует Ktor Client для HTTP запросов
- JWT токены для безопасной коммуникации
- Можно деплоить независимо

---

**Дата анализа:** 22.04.2026  
**Версии:** Backend Server (master), Face Recognition System (master)
