# Face Recognition Backend

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?logo=python)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.23-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.1.0-orange.svg)]()

REST API server for the **Miit_FaceDetect** face recognition system. Built with **FastAPI** and **SQLAlchemy**, providing admin authentication, employee management, face recognition via ArcFace ONNX, and application settings.

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
- [Contributing](#contributing)
- [License](#license)

## Features

- **Admin Authentication** — login, registration with invite codes, password reset via invite code, JWT Bearer token management
- **Employee Management** — CRUD operations, pagination, employee statistics
- **Face Recognition** — ArcFace ONNX model (512-dim embeddings), histogram fallback mode, image upload for recognition and registration
- **Application Settings** — runtime configuration of camera, notifications, match threshold, connection parameters
- **Rate Limiting** — endpoint protection via slowapi
- **Auto-initialization** — `.env`, database, and default settings created on first launch
- **Docker** — multi-stage build, healthcheck, automatic ArcFace model download

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | FastAPI | >=0.110.0 |
| Language | Python | >=3.10 |
| Package Manager | uv | — |
| ORM | SQLAlchemy | 2.0.23 |
| Migrations | Alembic | 1.13.1 |
| Database (dev) | SQLite | — |
| Database (prod) | PostgreSQL | — |
| Authentication | python-jose + bcrypt | 3.3.0 / 4.0.1 |
| Validation | Pydantic | >=2.0 |
| Face Detection | MediaPipe | 0.10.9 |
| Face Recognition | ArcFace ONNX + onnxruntime | >=1.16.0 |
| Image Processing | OpenCV | 4.10.0.84 |
| Rate Limiting | slowapi | 0.1.9 |
| Server | Uvicorn | 0.24.0 |
| Containerization | Docker | python:3.10-slim |

## Architecture

Layered architecture with strict dependency flow:

```
Client ──▶ Routers ──▶ Services ──▶ Database
                                    │
                             ┌──────▼──────┐
                             │ ArcFace ONNX│
                             └─────────────┘
```

| Layer | Responsibility |
|-------|----------------|
| **Routers** | HTTP endpoints, request validation (Pydantic), response serialization |
| **Services** | Business logic, face recognition, invite code management |
| **Database** | SQLAlchemy models, session management, data persistence |
| **Auth** | JWT token generation/verification, bcrypt password hashing |

**Cross-cutting:**
- **Dependency Injection** — FastAPI `Depends()` for authentication and DB sessions
- **Rate Limiting** — slowapi decorator on sensitive endpoints
- **Lifespan** — auto-initialization of `.env`, database, and settings on startup

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entry point, lifespan, middleware
│   ├── database.py          # SQLAlchemy session & DB initialization
│   ├── models.py            # SQLAlchemy models (Admin, Employee, AppSettings)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT authentication utilities
│   ├── deps.py              # FastAPI dependencies (get_current_admin)
│   ├── routers/
│   │   ├── admins.py        # Admin registration, login, password reset
│   │   ├── employees.py     # Employee CRUD operations
│   │   ├── faces.py         # Face recognition & registration
│   │   └── settings.py      # Application settings management
│   └── services/
│       ├── face_service.py  # Face recognition business logic
│       └── invite_service.py # Invite code system
├── alembic/                 # Database migration scripts
├── models/                  # ML models (arcface.onnx)
├── data/                    # SQLite database files
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Docker Compose configuration
├── entrypoint.sh            # Docker entrypoint script
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment variables template
└── MODELS.md                # Face recognition model documentation
```

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Required for runtime |
| uv | — | Package manager (`pip install uv`) |
| Docker | — | Optional, for containerized deployment |
| ArcFace ONNX | ~130 MB | Auto-downloaded in Docker; manual for local dev |

## Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd <repo-name>/backend
```

2. **Install dependencies**

```bash
uv sync
```

3. **Download ArcFace model** (for local development)

```bash
# Windows
Invoke-WebRequest -Uri "https://huggingface.co/garavv/arcface-onnx/resolve/main/arc.onnx?download=true" -OutFile "models/arcface.onnx"

# Linux/macOS
curl -L -o models/arcface.onnx "https://huggingface.co/garavv/arcface-onnx/resolve/main/arc.onnx?download=true"
```

## Usage

### Run in development mode

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The server starts at `http://localhost:8000`. API documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### First launch

On first startup, the system automatically:
1. Creates `.env` with generated `SECRET_KEY` and `INITIAL_INVITE_CODE`
2. Initializes the SQLite database
3. Creates default application settings

> **Important:** Copy the `INITIAL_INVITE_CODE` from the logs — it's required to register the first admin!

### Run with Docker

```bash
cd backend
docker compose up -d
```

The ArcFace model is downloaded automatically on first container startup.

### Build Docker image

```bash
docker build -t face-recognition-api ./backend
```

### Run database migrations

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
| `DATABASE_URL` | Database connection URL | `sqlite:///./data/faces.db` |
| `MODEL_DIR` | Face recognition models directory | `models` |
| `INITIAL_INVITE_CODE` | First admin registration code | auto-generated |
| `RESET_INVITE_CODE` | Admin password reset code | — |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

### Face Recognition Model

| Mode | Model | Input | Output | Accuracy |
|------|-------|-------|--------|----------|
| Primary | ArcFace ONNX (ResNet-100) | 112x112 RGB | 512-dim embedding | High |
| Fallback | Histogram | 96x96 grayscale | 64-bin → 512-dim | Low (testing only) |

The fallback mode activates automatically if `arcface.onnx` is not found.

## API Reference

**Base URL:** `http://localhost:8000`

### Authentication

| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| POST | `/admins/register` | — | `{username, email, password, invite_code}` | `{id, username, email, created_at}` |
| POST | `/admins/login` | — | `{username, password}` | `{access_token, token_type}` |
| GET | `/admins/me` | Yes | — | `{id, username, email, created_at}` |
| POST | `/admins/reset-password` | — | `{username, invite_code, new_password}` | `200 OK` |

### Employees

| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| POST | `/employees/` | Yes | `{employee_id, username, email, department, ...}` | `{EmployeeResponse}` |
| GET | `/employees/` | Yes | Query: `skip`, `limit` | `[{EmployeeResponse}]` |
| GET | `/employees/{id}` | Yes | — | `{EmployeeResponse}` |
| PUT | `/employees/{id}` | Yes | `{EmployeeUpdate}` | `{EmployeeResponse}` |
| DELETE | `/employees/{id}` | Yes | — | `204` |
| GET | `/employees/stats` | Yes | — | `{total, active, inactive}` |

### Face Recognition

| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| POST | `/faces/recognize` | Yes | Multipart (image) | `{faces_detected, results}` |
| POST | `/faces/register` | Yes | Multipart (image, employee_id) | `200 OK` |

### Settings

| Method | Endpoint | Auth | Body | Response |
|--------|----------|------|------|----------|
| GET | `/settings/` | Yes | — | `{AppSettings}` |
| PUT | `/settings/` | Yes | `{AppSettingsUpdate}` | `{AppSettings}` |

### Health Check

| Method | Endpoint | Auth | Response |
|--------|----------|------|----------|
| GET | `/health` | — | `{status: "healthy", service, version}` |
| GET | `/` | — | `{message, version, docs}` |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.
