# Face Recognition Backend

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?logo=python)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.23-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.0.0-orange.svg)]()


English | [Русский](README.ru.md)

REST API server for the **Miit_FaceDetect** face recognition system. Built with **FastAPI** and **SQLAlchemy**, providing admin authentication, employee management, face recognition via insightface + AdaFace IR-101, and application settings.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Admin Authentication** — login, registration with invite codes, password reset, JWT Bearer tokens
- **Employee Management** — CRUD operations, pagination, search, statistics
- **Face Recognition** — insightface SCRFD detector + AdaFace IR-101 (512-dim float32 embeddings), CLAHE preprocessing, 5-point face alignment, multi-photo registration (3-5 photos with embedding averaging)
- **Embedding Encryption** — AES-256-GCM encryption at rest with backward-compatible deserialization
- **Face Detection** — SCRFD-10GF with confidence threshold, automatic landmark detection
- **Application Settings** — runtime configuration of match threshold, camera, notifications
- **Rate Limiting** — endpoint protection via slowapi
- **Auto-initialization** — `.env`, database, and default settings created on first launch
- **Docker** — multi-stage build, healthcheck, insightface model auto-download
- **Tests** — pytest test suite with 50 tests

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | FastAPI | 0.110.0 |
| Language | Python | 3.10+ |
| Package Manager | uv | — |
| ORM | SQLAlchemy | 2.0.23 |
| Migrations | Alembic | 1.13.1 |
| Database | SQLite | built-in |
| Authentication | python-jose + bcrypt | 3.3.0 / 4.0.1 |
| Encryption | cryptography | 42.0.0 |
| Validation | Pydantic | 2.10.0 |
| Face Detection | insightface SCRFD-10GF | 0.7.3 |
| Face Recognition | AdaFace IR-101 / ArcFace R50 | ONNX |
| Preprocessing | OpenCV (headless) | 4.8.0.76 |
| Inference | onnxruntime | 1.16.0 |
| Rate Limiting | slowapi | 0.1.9 |
| Server | Uvicorn | 0.24.0 |
| Containerization | Docker | python:3.10-slim |

## Architecture

```
Client ──▶ Routers ──▶ Services ──▶ Database
                            │
                    ┌───────▼───────┐
                    │  insightface   │
                    │  (SCRFD +      │
                    │  AdaFace/ArcR50)│
                    └───────────────┘
```

| Layer | Responsibility |
|-------|----------------|
| **Routers** | HTTP endpoints, request validation (Pydantic), response serialization |
| **Services** | Business logic, face recognition pipeline, embedding encryption/serialization |
| **Database** | SQLAlchemy models, session management, data persistence |
| **Auth** | JWT token generation/verification, bcrypt password hashing |

**Key design decisions:**
- **Singleton service** — one `FaceRecognitionService` instance shared across the app via `app.state`
- **CLAHE preprocessing** — applied to full image before detection for low-light enhancement
- **float32 embeddings** — 2048 bytes each, encrypted at rest with AES-256-GCM, with safe deserialization helper for legacy float64
- **Dynamic threshold** — match threshold from `AppSettings` instead of hardcoded value

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entry point, lifespan, middleware
│   ├── database.py          # SQLAlchemy session & DB initialization
│   ├── models.py            # SQLAlchemy models (Admin, Employee, AppSettings)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT authentication utilities
│   ├── deps.py              # FastAPI dependencies (get_current_admin, get_face_service)
│   ├── routers/
│   │   ├── admins.py        # Admin registration, login, password reset
│   │   ├── employees.py     # Employee CRUD + face registration
│   │   ├── faces.py         # Face recognition endpoint
│   │   └── settings.py      # Application settings management
│   └── services/
│       ├── face_service.py  # Face recognition pipeline (insightface + AdaFace)
│       ├── crypto.py        # AES-256-GCM encryption/decryption for embeddings
│       ├── embedding.py     # Embedding serialization with encryption (float32 → encrypted blob)
│       └── invite_service.py # Invite code system
├── alembic/                 # Database migration scripts
├── data/                    # Database files (gitignored)
├── models/                  # ONNX models (gitignored, adaface_ir101.onnx)
├── tests/                   # pytest test suite
│   ├── conftest.py          # Test client, in-memory SQLite, fixtures
│   ├── test_admins.py       # Admin endpoint tests
│   ├── test_health.py       # Health endpoint tests
│   ├── test_clahe.py        # CLAHE preprocessing tests
│   ├── test_embedding.py    # Embedding encryption/serialization tests
│   ├── test_crypto.py        # AES-256-GCM encryption tests
│   ├── test_employees.py     # Multi-photo registration tests
│   └── test_singleton.py    # Service singleton test
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Docker Compose configuration
├── entrypoint.sh            # Docker entrypoint (insightface model download)
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment variables template
├── MODELS.md                # Face recognition model documentation
└── BACKEND_SETUP.md         # Deployment guide (Russian)
```

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Required for runtime |
| uv | — | Package manager (`pip install uv`) |
| C++ compiler | — | Required for insightface Cython extension (MSVC on Windows, gcc/g++ on Linux) |
| Docker | — | Optional, for containerized deployment |

## Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd <repo-name>/backend
```

2. **Install dependencies**

```bash
uv sync
uv sync --group dev   # for testing
```

3. **Download insightface models** (for local development)

The `buffalo_l` model pack downloads automatically on first run (~32 MB). For Docker, it's handled by `entrypoint.sh`.

## Usage

### Run in development mode

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The server starts at `http://localhost:8000`. API documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### First launch

On first startup, the system automatically:
1. Creates `.env` with generated `SECRET_KEY`, `ENCRYPTION_KEY`, and `INITIAL_INVITE_CODE`
2. Initializes the SQLite database
3. Downloads insightface `buffalo_l` models on first face recognition request
4. Creates default application settings

> **Important:** Copy the `INITIAL_INVITE_CODE` from the logs — it's required to register the first admin!

### Run with Docker

```bash
cd backend
docker compose build
docker compose up -d
```

Insightface models are downloaded automatically on first container startup.

### Run tests

```bash
uv run pytest tests/ -v
```

### Database migrations

```bash
# Apply migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Rollback
uv run alembic downgrade -1
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | auto-generated |
| `ENCRYPTION_KEY` | AES-256-GCM key for embedding encryption (base64) | auto-generated |
| `DATABASE_URL` | Database connection URL | `sqlite:///./data/faces.db` |
| `INITIAL_INVITE_CODE` | First admin registration code | auto-generated |
| `RESET_INVITE_CODE` | Admin password reset code | — |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

### Face Recognition Pipeline

| Step | Component | Details |
|------|-----------|---------|
| 1. Preprocessing | CLAHE | BGR→LAB, clipLimit=2.0, tileGridSize=(8,8) |
| 2. Detection | SCRFD-10GF | 5-point landmarks, confidence threshold |
| 3. Alignment | norm_crop | 5-point similarity transform → 112×112 |
| 4. Recognition | AdaFace IR-101 / ArcFace R50 | 512-dim float32 embedding |
| 5. Comparison | Cosine similarity | Matrix-vector multiply, threshold from settings |

### Embedding Encryption

Embeddings are encrypted at rest using **AES-256-GCM** before being stored in the database.

| Property | Value |
|----------|-------|
| Algorithm | AES-256-GCM (authenticated encryption) |
| Key | 256-bit, stored as base64 in `ENCRYPTION_KEY` env var |
| Nonce | 12 random bytes per encryption (different ciphertext each time) |
| Format | `[0x01 version][12B nonce][ciphertext + 16B GCM tag]` |
| Overhead | 29 bytes per embedding (1 + 12 + 16) |
| Backward compatibility | Legacy unencrypted float32/float64 embeddings auto-detected by absence of `0x01` prefix |

> **Note:** Changing `ENCRYPTION_KEY` makes existing embeddings unreadable. Keep it safe and backed up.

### Embedding Format

| Property | Value |
|----------|-------|
| Dimension | 512 |
| Data type | float32 |
| Size (raw) | 2048 bytes per embedding |
| Size (encrypted) | 2077 bytes per embedding (2048 + 29 overhead) |
| Storage | SQLite BLOB (encrypted) |
| Legacy support | Auto-detects and converts unencrypted float32/float64 |

## API Reference

**Base URL:** `http://localhost:8000`

### Authentication

| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| POST | `/api/v1/admins/register` | — | `{username, email, password, invite_code}` | `{id, username, email, created_at}` |
| POST | `/api/v1/admins/login` | — | `{username, password}` | `{access_token, token_type}` |
| GET | `/api/v1/admins/me` | Yes | — | `{id, username, email, created_at}` |
| POST | `/api/v1/admins/reset-password` | — | `{username, invite_code, new_password}` | `200 OK` |
| POST | `/api/v1/admin/invites` | Yes | `{expires_hours}` | `{id, code, created_by, ...}` |
| GET | `/api/v1/admin/invites` | Yes | — | `{codes: [{InviteCodeResponse}], total: number}` |
| DELETE | `/api/v1/admin/invites/{id}` | Yes | — | `200 OK` |

### Employees

| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| POST | `/api/v1/employees/register` | Yes | Multipart (3-5 images + form) | `{EmployeeResponse}` |
| POST | `/api/v1/employees/{employee_id}/re-embed` | Yes | Multipart (3-5 images) | `{EmployeeResponse}` |
| GET | `/api/v1/employees` | Yes | Query: `skip`, `limit` | `[{EmployeeResponse}]` |
| GET | `/api/v1/employees/search` | Yes | Query: `q` | `[{EmployeeResponse}]` |
| GET | `/api/v1/employees/stats` | Yes | — | `{total, active, inactive}` |
| PUT | `/api/v1/employees/{employee_id}` | Yes | `{EmployeeUpdate}` | `{EmployeeResponse}` |
| DELETE | `/api/v1/employees/{employee_id}` | Yes | — | `200 OK` |

### Face Recognition

| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| POST | `/api/v1/faces/recognize` | Yes | Multipart (image) | `{faces_detected, results}` |

### Settings

| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| GET | `/api/v1/settings` | Yes | — | `{AppSettings}` |
| PUT | `/api/v1/settings` | Yes | `{AppSettingsUpdate}` | `{AppSettings}` |
| POST | `/api/v1/settings/backup` | Yes | — | `{message, backup_path}` |

### Health Check

| Method | Endpoint | Auth | Response |
|--------|----------|------|----------|
| GET | `/health` | — | `{status: "healthy", service, version}` |
| GET | `/` | — | `{message}` |

## Changelog — v5.0.0

- **insightface + AdaFace IR-101** replaces MediaPipe + ArcFace
- **Multi-photo registration** — 3-5 photos per employee, embeddings averaged (mean + L2-norm)
- **Re-embed endpoint** — `POST /employees/{id}/re-embed` to update face embeddings
- **Embedding encryption** — AES-256-GCM at rest, with backward-compatible legacy deserialization
- **CLAHE preprocessing** for low-light face detection
- **float32 embeddings** instead of float64 (half the storage)
- **Dynamic match threshold** from AppSettings instead of hardcoded 0.4
- **Singleton FaceRecognitionService** via app.state instead of two module-level instances
- **Unified `detect_and_embed()` API** instead of separate `detect_faces()` + `get_face_embedding()`
- **pytest test suite** with 50 tests

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.
