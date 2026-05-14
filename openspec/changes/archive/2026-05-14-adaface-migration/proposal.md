## Why

Current face recognition pipeline has critical architectural and data integrity issues: dual `FaceRecognitionService` instances waste memory (2 ONNX sessions), embeddings stored as `np.float64` cause silent corruption when mixed with `float32`, hardcoded threshold `0.4` ignores `AppSettings.match_threshold`, no face alignment before embedding extraction, a useless histogram fallback inflates code, and `opencv-python` conflicts with headless deployments. Zero test coverage makes any change risky.

## What Changes

- **BREAKING**: Replace MediaPipe (face detection) + custom ArcFace ONNX (embeddings) with **insightface** (SCRFD detection + 5-point alignment) + **AdaFace IR-101** (recognition)
- **BREAKING**: Switch embedding dtype from `float64` to `float32` — existing embeddings are incompatible, database will be cleared
- **BREAKING**: Remove histogram fallback entirely — no alternatives, production-only
- **BREAKING**: Remove `MODEL_DIR` env var and ArcFace model download logic
- Single `FaceRecognitionService` instance via `app.state` (instead of two module-level singletons)
- Dynamic threshold from `AppSettings.match_threshold` instead of hardcoded `0.4`
- CLAHE preprocessing on full image before detection (improves low-light conditions)
- Safe embedding deserialization with size validation and automatic `float64` → `float32` migration
- `Employee.embedding` becomes `nullable=True`
- Replace `opencv-python` with `opencv-python-headless`
- Add pytest infrastructure (`tests/conftest.py`, smoke tests)
- Add `scripts/convert_adaface_to_onnx.py` for AdaFace IR-101 PyTorch → ONNX conversion
- Docker: remove ArcFace download, add insightface model cache volume
- Version bump: `4.1.0` → `5.0.0`

## Capabilities

### New Capabilities
- `face-service-v2`: insightface + AdaFace IR-101 service — detection (SCRFD), alignment (5-point similarity transform), recognition (AdaFace IR-101 512-dim float32), CLAHE preprocessing, singleton lifecycle, safe embedding serialization
- `embedding-serialization`: float32 storage with validation, automatic float64 legacy migration, serialize/deserialize helpers
- `test-infrastructure`: pytest configuration, in-memory test DB, test JWT auth, smoke tests for all endpoints

### Modified Capabilities
- `api-routes`: dynamic threshold from settings, singleton dependency injection, bbox format conversion (x1y1x2y2 → xywh), removed module-level service instantiation

## Impact

- **Code**: `face_service.py` complete rewrite, `models.py` (embedding nullable), `faces.py` + `employees.py` (new service API), `main.py` (lifespan init), `deps.py` (new dependency), `database.py` (env template), new `embedding.py` module
- **API**: Response schema unchanged; bbox stays `[x, y, w, h]`; all existing endpoints preserved
- **Dependencies**: Remove `mediapipe`, `opencv-python`; Add `insightface`, `opencv-python-headless`, `pytest`/`pytest-asyncio`/`httpx` (dev)
- **Database**: All employee embeddings invalidated (different model + dtype); clean slate
- **Docker**: entrypoint.sh, Dockerfile, docker-compose.yml updated for insightface model cache
- **Migration**: `scripts/convert_adaface_to_onnx.py` (run once, separate from app)