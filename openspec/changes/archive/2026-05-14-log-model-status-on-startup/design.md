## Context

The `FaceRecognitionService` initializes during module import in `faces.py`, before the FastAPI app starts. Model loading (ArcFace ONNX or fallback) happens in `__init__`, with status reported via `print()` statements. The `lifespan` function in `main.py` already logs startup events using structured logging, but has no visibility into which recognition engine is active.

## Goals / Non-Goals

**Goals:**
- Expose model status from `FaceRecognitionService` as a queryable property
- Log model status during server startup using the structured logger
- Make it immediately clear in logs whether ArcFace or fallback mode is active

**Non-Goals:**
- No API endpoint changes
- No changes to model loading logic or fallback behavior
- No runtime model switching

## Decisions

1. **Add `model_name` property to `FaceRecognitionService`**: Returns `"arcface_onnx"` if `embedding_net` is not None, `"histogram_fallback"` otherwise. Simple, no new state needed.

2. **Log in lifespan after FaceRecognitionService is already initialized**: The service is a module-level singleton in `faces.py`, so it's already loaded before lifespan runs. We just need to import it and read the property.

3. **Use existing logger in `main.py`**: Consistent with other startup messages (`"Initializing database..."`, `"Face Recognition API starting up..."`).

## Risks / Trade-offs

- **Circular import risk**: `FaceRecognitionService` is in `services/face_service.py` and `main.py` already imports from `routers/faces.py` which imports the service. Importing directly in lifespan should be safe since modules are already loaded by then.
- **Module-level singleton**: The service is created at import time, so any model download happens before lifespan. This is existing behavior, not changed here.
