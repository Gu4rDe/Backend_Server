## Why

Multi-stage Docker builds copy the venv from /build/.venv to /app/.venv, but all venv scripts (uvicorn, lembic, etc.) contain hardcoded shebang lines pointing to /build/.venv/bin/python. This path doesn't exist at runtime, causing "cannot execute: required file not found" errors. A partial workaround (python -m uvicorn) fixes the server but leaves all other venv scripts broken.

## What Changes

- Add --relocatable flag to uv sync in the Dockerfile so venv scripts use portable shebangs
- Remove the python -m uvicorn workaround in entrypoint.sh (no longer needed)
- Add a fallback sed patch step in the Dockerfile in case --relocatable doesn't fully resolve the issue

## Capabilities

### New Capabilities

- env-relocatable-build: Ensures all venv scripts in the Docker image use correct runtime shebangs after multi-stage copy

### Modified Capabilities

_(none)_

## Impact

- ackend/Dockerfile — uv sync command and optional post-copy sed patch
- ackend/entrypoint.sh — revert python -m uvicorn back to direct uvicorn call
- Docker image rebuild required after the change
