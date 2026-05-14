## Why

Currently, the `FaceRecognitionService` prints model load status using plain `print()` statements during initialization. These messages are easy to miss in production logs and don't follow the project's structured logging pattern. Operators have no reliable way to verify which recognition engine (ArcFace ONNX or fallback histogram) is active when the server starts.

## What Changes

- Add a startup log message in the `lifespan` function that reports the active face recognition model
- The message will clearly indicate whether ArcFace ONNX or fallback histogram mode is in use
- Use the existing structured logger for consistency with other startup messages

## Capabilities

### New Capabilities
- `model-status-logging`: Logs the active face recognition model (ArcFace ONNX or fallback histogram) during server startup

### Modified Capabilities
<!-- No existing capabilities are modified -->

## Impact

- `backend/app/main.py` — lifespan function will log model status
- `backend/app/services/face_service.py` — `FaceRecognitionService` will expose model status property
- No API changes, no breaking changes
