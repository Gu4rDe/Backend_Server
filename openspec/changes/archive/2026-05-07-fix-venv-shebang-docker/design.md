## Context

The project uses a multi-stage Docker build where uv creates a venv in /build/.venv (builder stage) that is then copied to /app/.venv (runtime stage). The COPY --from=builder /build/.venv /app/.venv instruction preserves the original absolute paths in venv script shebangs, which point to /build/.venv/bin/python — a path that doesn't exist in the runtime container.

Currently, entrypoint.sh works around this by calling .venv/bin/uvicorn directly (which relies on PATH), but other venv scripts like lembic are invoked with their shebang and fail.

## Goals / Non-Goals

**Goals:**
- Fix all venv script shebangs so they work correctly in the runtime container
- Ensure lembic and any other venv scripts work alongside uvicorn
- Make the Docker build self-contained — no runtime workarounds needed

**Non-Goals:**
- Changing the multi-stage build strategy (builder + runtime is fine)
- Switching from uv to another package manager
- Modifying application code

## Decisions

### Decision 1: Use uv sync --relocatable as the primary fix

**Choice**: Add --relocatable flag to uv sync in the Dockerfile builder stage.

**Rationale**: The --relocatable flag tells uv to generate shebangs that use python3 relative to the venv's own in/ directory rather than hardcoding the absolute build path. This is the cleanest fix — one flag, no post-processing needed.

**Alternatives considered**:
- **sed patch after COPY**: Fragile, needs maintenance if venv structure changes. Reserved as fallback.
- **python -m calls**: Only fixes individual scripts, not the root cause.
- **Single-stage build**: Defeats the purpose of multi-stage (smaller image).

### Decision 2: Add a sed fallback step after COPY

**Choice**: Add a RUN find ... | sed step after the COPY --from=builder line as a safety net.

**Rationale**: If --relocatable doesn't fully resolve all shebangs (edge cases with older uv versions), the sed step catches any remaining /build/ references. Belt and suspenders approach.

### Decision 3: Revert entrypoint.sh to use uvicorn directly

**Choice**: Keep .venv/bin/uvicorn app.main:app in entrypoint.sh (current code already does this via PATH).

**Rationale**: With --relocatable, the shebang in the uvicorn script will be correct, so direct invocation works. No python -m workaround needed.

## Risks / Trade-offs

- **--relocatable compatibility**: Older uv versions may not support this flag → the sed fallback covers this case
- **sed step adds a Docker layer**: Minimal impact (a few KB), but adds a RUN layer to the image
- **PATH reliance**: The runtime container sets PATH="/app/.venv/bin:", so even with broken shebangs the scripts can be found by shell — but shebangs are used when scripts are executed directly
