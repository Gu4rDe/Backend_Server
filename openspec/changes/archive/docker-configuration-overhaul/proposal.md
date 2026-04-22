# Proposal: Docker Configuration Overhaul

## Why
Existing Docker setup was minimal — single-stage build, no healthcheck, no docker-compose, basic entrypoint script. Needed comprehensive improvements for production readiness and developer experience.

## What
- **Multi-stage Dockerfile** — reduced image size, separated build from runtime
- **docker-compose.yml** — one-command deployment with volumes and healthcheck
- **Improved entrypoint.sh** — structured logging with [INFO]/[ERROR]/[WARN] prefixes
- **Expanded .dockerignore** — excluded IDE files, caches, temp files
- **README.md Docker section** — complete documentation with commands and configuration details

### Changes
- `Dockerfile` — multi-stage build, non-root user, healthcheck, bytecode compilation
- `docker-compose.yml` — new file with volumes, healthcheck, log rotation, restart policy
- `entrypoint.sh` — formatted logging, model auto-download, .env validation
- `.dockerignore` — added .vscode/, .idea/, *.swp, linter caches
- `README.md` — added comprehensive Docker section

### Files modified
- `backend/Dockerfile`
- `backend/docker-compose.yml` (new)
- `backend/entrypoint.sh`
- `backend/.dockerignore`
- `README.md`

## Impact
- **Breaking changes**: None
- **Migration needed**: No
- **Image size**: Reduced via multi-stage build
- **Security**: Non-root user, healthcheck enabled
