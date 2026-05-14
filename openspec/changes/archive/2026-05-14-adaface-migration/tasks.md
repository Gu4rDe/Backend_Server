## 1. Preparation

- [x] 1.1 Create git branch `feature/adaface-migration`
- [x] 1.2 Add pytest dev dependencies to `pyproject.toml`: `pytest>=7.0`, `pytest-asyncio>=0.21`, `httpx>=0.24`
- [ ] 1.3 Create `tests/conftest.py` with TestClient, in-memory SQLite, test JWT auth, test admin user
- [ ] 1.4 Create `tests/test_health.py` — health endpoint smoke test
- [ ] 1.5 Create `tests/test_admins.py` — admin registration and login smoke test
- [ ] 1.6 Run tests, confirm all pass

## 2. Singleton FaceRecognitionService

- [ ] 2.1 Add `get_face_service()` dependency function in `app/deps.py` (returns `request.app.state.face_service`)
- [ ] 2.2 Move `FaceRecognitionService` initialization to `app/main.py` lifespan (store on `app.state.face_service`)
- [ ] 2.3 Update `app/routers/faces.py` to use `Depends(get_face_service)` instead of module-level instance
- [ ] 2.4 Update `app/routers/employees.py` to use `Depends(get_face_service)` instead of module-level instance
- [ ] 2.5 Remove module-level `face_service = FaceRecognitionService(...)` from both routers
- [ ] 2.6 Write test: verify both routers receive same service instance
- [ ] 2.7 Run tests

## 3. CLAHE Preprocessing

- [ ] 3.1 Add `apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)) -> np.ndarray` to `face_service.py`
- [ ] 3.2 Integrate CLAHE into `detect_faces()` — apply before MediaPipe detection
- [ ] 3.3 Integrate CLAHE into employee registration path (before face detection)
- [ ] 3.4 Write test: CLAHE preserves image shape and dtype
- [ ] 3.5 Run tests

## 4. Dependency Swap

- [ ] 4.1 Remove `mediapipe==0.10.9` from `pyproject.toml`
- [ ] 4.2 Replace `opencv-python==4.10.0.84` with `opencv-python-headless>=4.8.0` in `pyproject.toml`
- [ ] 4.3 Add `insightface>=0.7.3` to `pyproject.toml`
- [ ] 4.4 Run `uv sync` and resolve dependency conflicts
- [ ] 4.5 Write test: `import insightface` succeeds
- [ ] 4.6 Run tests

## 5. AdaFace ONNX Conversion Script

- [ ] 5.1 Create `scripts/convert_adaface_to_onnx.py`
- [ ] 5.2 Implement `AdaFaceONNXWrapper` class (strips norm output, keeps only 512-dim embedding)
- [ ] 5.3 Implement download logic for IR-101 MS1MV3 weights from Google Drive
- [ ] 5.4 Implement ONNX export with `torch.onnx.export` (input 1×3×112×112, opset 11, dynamic_axes for batch)
- [ ] 5.5 Add validation: load with `onnxruntime.InferenceSession`, verify output shape is (1, 512)
- [ ] 5.6 Document conversion steps in script comments
- [ ] 5.7 Convert the model and verify `models/adaface_ir101.onnx` is produced

## 6. Rewrite FaceRecognitionService

- [ ] 6.1 Remove all MediaPipe imports and code from `face_service.py`
- [ ] 6.2 Remove ArcFace direct loading, `MODEL_URL`, `_load_model()`, `download_model()`, histogram fallback
- [ ] 6.3 Implement new `FaceRecognitionService.__init__`: load `FaceAnalysis(name="buffalo_l")`, prepare with `ctx_id`, load AdaFace ONNX via `insightface.model_zoo.get_model()`, replace `app.models["recognition"]`
- [ ] 6.4 Implement `detect_and_embed(image, conf_threshold=0.5) -> list[FaceResult]`: CLAHE → `app.get()` → filter by confidence → return list of `FaceResult(bbox_xywh, embedding_float32, confidence)`
- [ ] 6.5 Convert bbox from insightface format `[x1,y1,x2,y2]` to API format `[x,y,w,h]` inside `detect_and_embed`
- [ ] 6.6 Keep `compare_faces_batch()` method unchanged (matrix-vector multiply)
- [ ] 6.7 Update `model_status` property to report "insightface SCRFD + AdaFace IR-101"
- [ ] 6.8 Define `FaceResult` dataclass (bbox, embedding, confidence)
- [ ] 6.9 Write tests: `detect_and_embed` returns correct structure, `compare_faces_batch` works, CLAHE unit test
- [ ] 6.10 Run tests

## 7. Embedding Serialization & DB Migration

- [ ] 7.1 Create `app/services/embedding.py` with `serialize_embedding()`, `deserialize_embedding()`, `validate_embedding()`
- [ ] 7.2 Change `Employee.embedding` from `nullable=False` to `nullable=True` in `app/models.py`
- [ ] 7.3 Delete `data/faces.db` (clean slate — incompatible embeddings)
- [ ] 7.4 Create Alembic migration for `embedding nullable=True`
- [ ] 7.5 Update `app/routers/faces.py`: use `deserialize_embedding()` instead of `np.frombuffer(..., dtype=np.float64)`
- [ ] 7.6 Update `app/routers/employees.py`: use `serialize_embedding()` instead of `embedding.tobytes()`
- [ ] 7.7 Write tests: round-trip float32 serialization, float64 legacy migration, ValueError on invalid size
- [ ] 7.8 Run tests

## 8. Dynamic Threshold & Router Updates

- [ ] 8.1 Update `faces.py` `/recognize`: read `match_threshold` from `db.query(AppSettings).first().match_threshold`, fallback to 0.4
- [ ] 8.2 Update `faces.py`: use `detect_and_embed()` instead of separate `detect_faces()` + `get_face_embedding()`
- [ ] 8.3 Update `employees.py` `/register`: use `detect_and_embed()` instead of separate calls
- [ ] 8.4 Update `employees.py`: use `serialize_embedding()` for storage
- [ ] 8.5 Remove `detect_faces()` and `get_face_embedding()` methods from `FaceRecognitionService` (replaced by `detect_and_embed()`)
- [ ] 8.6 Write integration tests for `/api/v1/faces/recognize` and `/api/v1/employees/register`
- [ ] 8.7 Run tests

## 9. Docker & Infrastructure

- [ ] 9.1 Update `entrypoint.sh`: remove ArcFace download, add insightface model pre-download (Python one-liner)
- [ ] 9.2 Update `Dockerfile`: add `~/.insightface` directory, adjust model volume paths
- [ ] 9.3 Update `docker-compose.yml`: replace `face-models:/app/models` with insightface cache volume
- [ ] 9.4 Update `.env.example`: remove or make `MODEL_DIR` optional
- [ ] 9.5 Update `app/database.py`: remove `MODEL_DIR` from `.env` auto-generation template
- [ ] 9.6 Update `.gitignore`: add insightface cache, adjust `*.onnx` patterns, add `models/adaface_ir101.onnx`
- [ ] 9.7 Run tests

## 10. Cleanup & Finalization

- [ ] 10.1 Remove `download_model()` function and `MODEL_URL` constant from `face_service.py`
- [ ] 10.2 Update `MODELS.md` with insightface + AdaFace documentation
- [ ] 10.3 Bump version in `app/main.py`: `4.1.0` → `5.0.0` (in app title, health endpoint, and version string)
- [ ] 10.4 Update `BACKEND_SETUP.md` if needed
- [ ] 10.5 Final full test suite run
- [ ] 10.6 Git commit with detailed message