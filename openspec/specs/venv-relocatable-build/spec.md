## ADDED Requirements

### Requirement: Relocatable venv in Docker build
The `uv sync` command in the Dockerfile builder stage SHALL include the `--relocatable` flag so that all venv scripts use portable shebangs instead of hardcoded build-stage paths.

#### Scenario: venv scripts use relocatable shebangs
- **WHEN** `uv sync --frozen --no-dev --no-editable --compile-bytecode --relocatable` is run in the builder stage
- **THEN** all scripts in `.venv/bin/` use a shebang that resolves correctly at `/app/.venv/bin/python` in the runtime container

#### Scenario: uvicorn shebang is correct after copy
- **WHEN** the builder venv is copied from `/build/.venv` to `/app/.venv`
- **THEN** `/app/.venv/bin/uvicorn` contains a shebang pointing to `/app/.venv/bin/python` rather than `/build/.venv/bin/python`

#### Scenario: alembic shebang is correct after copy
- **WHEN** the builder venv is copied from `/build/.venv` to `/app/.venv`
- **THEN** `/app/.venv/bin/alembic` contains a shebang pointing to `/app/.venv/bin/python` rather than `/build/.venv/bin/python`

### Requirement: Shebang fallback patch in Dockerfile
The Dockerfile SHALL include a `RUN` step after the venv copy that replaces any remaining `/build/.venv/bin/python` references in shebangs with `/app/.venv/bin/python`.

#### Scenario: sed patch replaces stale shebangs
- **WHEN** the Dockerfile reaches the runtime stage after `COPY --from=builder /build/.venv /app/.venv`
- **THEN** a `RUN` command executes `find /app/.venv/bin -type f | xargs grep -l "#!/build/.venv/bin/python" | xargs sed -i 's|#!/build/.venv/bin/python|#!/app/.venv/bin/python|g'`

#### Scenario: sed patch is a no-op when shebangs are already correct
- **WHEN** `--relocatable` produces correct shebangs and no files match the `/build/` pattern
- **THEN** the `sed` step completes without errors and makes no changes

### Requirement: Direct uvicorn invocation in entrypoint
The `entrypoint.sh` script SHALL invoke `uvicorn` directly via `.venv/bin/uvicorn` without the `python -m` workaround.

#### Scenario: entrypoint starts uvicorn directly
- **WHEN** `entrypoint.sh` runs in the Docker container
- **THEN** it executes `.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`
