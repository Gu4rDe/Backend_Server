## 1. Dockerfile Changes

- [x] 1.1 Add `--relocatable` flag to `uv sync` command in the builder stage of `backend/Dockerfile`
- [x] 1.2 Add `RUN` step after `COPY --from=builder /build/.venv /app/.venv` to patch any remaining stale shebangs with `sed`

## 2. Entrypoint Cleanup

- [x] 2.1 Verify `entrypoint.sh` uses `.venv/bin/uvicorn` directly (not `python -m uvicorn` workaround) and update if needed

## 3. Verification

- [x] 3.1 Rebuild Docker image and verify shebangs: `head -1 /app/.venv/bin/uvicorn` and `head -1 /app/.venv/bin/alembic` both show `#!/app/.venv/bin/python`
- [x] 3.2 Verify API health check works: `curl http://localhost:8000/health`
- [x] 3.3 Verify `alembic` works inside container: `docker compose run --rm --entrypoint bash api -c `.venv/bin/alembic --help`'

