# Project Context

## Purpose
Backend API server for a face recognition system with admin authentication, employee management, and real-time face recognition capabilities.

## Tech Stack
- **Framework**: FastAPI >=0.110.0
- **Language**: Python >=3.10
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Database**: SQLite (development), PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0.23
- **Migrations**: Alembic 1.13.1
- **Authentication**: JWT (python-jose), bcrypt password hashing
- **Validation**: Pydantic >=2.0
- **Face Recognition**: MediaPipe 0.10.9, OpenCV 4.10.0.84, ArcFace ONNX model
- **Rate Limiting**: slowapi 0.1.9
- **Server**: Uvicorn 0.24.0
- **Containerization**: Docker (python:3.10-slim)

## Project Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI entry point, lifespan, middleware
│   ├── database.py          # SQLAlchemy session & DB initialization
│   ├── models.py            # SQLAlchemy models (Admin, Employee, AppSettings, InviteCode)
│   ├── schemas.py           # Pydantic schemas for request/response validation
│   ├── auth.py              # JWT authentication utilities
│   ├── deps.py              # FastAPI dependencies (get_current_admin)
│   ├── routers/
│   │   ├── admins.py        # Admin registration & login endpoints
│   │   ├── employees.py     # Employee CRUD operations
│   │   ├── faces.py         # Face recognition endpoints
│   │   └── settings.py      # Application settings management
│   └── services/
│       ├── face_service.py  # Face recognition business logic
│       └── invite_service.py # Invite code system
├── alembic/                 # Database migration scripts
├── models/                  # ML models (arcface.onnx)
├── data/                    # SQLite database files
├── Dockerfile               # Production Docker configuration
├── entrypoint.sh            # Docker entrypoint script
├── pyproject.toml           # Project dependencies & configuration
└── .env.example             # Environment variables template
```

## Architecture Patterns
- **Layered Architecture**: Routers → Services → Database
- **Dependency Injection**: FastAPI's `Depends()` for authentication & DB sessions
- **Service Layer**: Business logic isolated in `services/` directory
- **Schema Validation**: Pydantic models for all API inputs/outputs
- **State Management**: AppSettings model for runtime configuration

## API Endpoints
- `POST /admins/register` - Admin registration with invite code
- `POST /admins/login` - Admin authentication
- `GET /admins/me` - Current admin info
- `POST /employees/` - Create employee
- `GET /employees/` - List employees with pagination
- `GET /employees/{id}` - Get employee details
- `PUT /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Delete employee
- `GET /employees/stats` - Employee statistics
- `POST /faces/recognize` - Face recognition
- `POST /faces/register` - Register face for employee
- `GET /settings/` - Get application settings
- `PUT /settings/` - Update settings
- `GET /health` - Health check
- `GET /` - Root endpoint

## Data Models
- **Admin**: id, username, email, password_hash, created_at
- **AdminInviteCode**: id, code, created_by, used_by, used_at, expires_at, is_used, created_at
- **Employee**: id, employee_id, username, email, phone, department, position, location, hire_date, is_active, access_enabled, photo_path, embedding, created_at
- **AppSettings**: id, theme, fullscreen, camera_resolution, camera_fps, sound_notifications, access_notifications, match_threshold, two_factor_enabled, auto_backup, backend_url, connection_timeout, updated_at

## Security
- JWT token-based authentication
- Bcrypt password hashing
- Rate limiting on endpoints
- CORS middleware configuration
- Invite code system for admin registration
- Password validation (min 6, max 128 chars)
- Username validation (min 3, max 50 chars)

## Configuration
Environment variables (`.env`):
| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | auto-generated |
| `DATABASE_URL` | Database connection URL | `sqlite:///./data/faces.db` |
| `MODEL_DIR` | Face recognition models directory | `models` |
| `INITIAL_INVITE_CODE` | First admin registration code | auto-generated |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

## Development Commands
```bash
# Install dependencies
cd backend && uv sync

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run database migrations
uv run alembic upgrade head

# Build Docker image
docker build -t face-recognition-api ./backend
```

## Deployment
- Docker containerization with python:3.10-slim base
- Systemd service for production
- Nginx reverse proxy with SSL
- PostgreSQL migration support
- See `BACKEND_SETUP.md` for detailed deployment instructions

## External Dependencies
- ArcFace ONNX model for face recognition (requires manual download)
- MediaPipe for face detection
- OpenCV for image processing
- NumPy for numerical operations

## Testing
- No test framework currently configured
- Health check endpoint available at `/health`

## Version
Current API version: 4.1.0
