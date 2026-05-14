## Context

The backend runs a face recognition pipeline: MediaPipe for detection, a custom ArcFace ONNX (ResNet-100, 512-dim) for embeddings, stored as `np.float64` in SQLite. The service is instantiated twice (once per router), wasting memory. There is no face alignment, no test coverage, and a hardcoded threshold ignores DB settings.

The migration replaces this with insightface (SCRFD detector + 5-point alignment from buffalo_l pack) and AdaFace IR-101 (converted from PyTorch to ONNX). insightface handles detection, landmark extraction, and alignment internally — no separate alignment step needed.

Key constraints: the project uses Python 3.10, uv for package management, Docker for deployment, and SQLite in development. The AdaFace IR-101 ONNX model must be converted externally since insightface doesn't ship it.

## Goals / Non-Goals

**Goals:**
- Single FaceRecognitionService instance shared across the app
- insightface SCRFD detection with built-in 5-point face alignment
- AdaFace IR-101 512-dim float32 embeddings (no histogram fallback)
- Safe embedding deserialization (float64 legacy migration, size validation)
- Dynamic match threshold from AppSettings
- CLAHE preprocessing for low-light images
- Full pytest infrastructure with in-memory DB
- opencv-python-headless for Docker compatibility

**Non-Goals:**
- GPU/CUDA inference (CPU-only for now)
- Batch ONNX inference optimization
- Vector similarity index (FAISS, annoy) — brute-force O(n) is acceptable for current scale
- PostgreSQL migration (keep SQLite default)
- Frontend changes (API response format preserved)
- Re-training or fine-tuning the AdaFace model

## Decisions

### D1: insightface over custom detector + separate alignment

**Choice**: Use insightface's `FaceAnalysis` pipeline (SCRFD detection + 5-point landmark + `norm_crop` alignment) instead of separating detection and alignment into distinct modules.

**Rationale**: insightface handles alignment internally via `face_align.norm_crop()` using a similarity transform from detected keypoints. This eliminates the need for a `detector.py` module or manual alignment code. The 5-point landmarks (left eye, right eye, nose, left mouth, right mouth) are produced as part of detection at no extra cost.

**Alternatives considered**:
- Separate RetinaFace then manual alignment — more code, more error-prone
- BlazeFace from MediaPipe — inferior quality, no landmarks

### D2: AdaFace IR-101 via ONNX export script instead of bundled model

**Choice**: Provide `scripts/convert_adaface_to_onnx.py` that downloads PyTorch weights and exports to ONNX. The resulting `models/adaface_ir101.onnx` is gitignored and must be generated once.

**Rationale**: insightface doesn't ship AdaFace. The ONNX wrapper strips the `norm` output tuple, keeping only the 512-dim embedding. The model weight file is ~250MB in PyTorch format; exporting once to ~130MB ONNX is operationally simpler than shipping PyTorch and torch in production.

**Alternatives considered**:
- Bundle a pre-converted ONNX in the repo — too large for git
- Use insightface's default recognition (ArcFace R50 from buffalo_l) — acceptable fallback but lower quality than AdaFace IR-101

### D3: float32 embeddings with safe deserialization instead of data migration

**Choice**: Store all new embeddings as `np.float32` (2048 bytes). The `deserialize_embedding()` function auto-detects byte length: 2048 → float32, 4096 → float64 (legacy) → cast to float32. Database is cleared anyway since embeddings are model-incompatible.

**Rationale**: float32 halves storage and avoids the silent corruption bug where `np.frombuffer(data, dtype=np.float64)` on float32 data reads half the values with wrong offsets. Since the DB is being cleared (incompatible models), there's no data to migrate in-place.

### D4: singleton via FastAPI app.state instead of module-level instantiation

**Choice**: Initialize `FaceRecognitionService` in `main.py` lifespan, store on `app.state.face_service`. Routers access via `Depends(get_face_service)`.

**Rationale**: Guarantees exactly one ONNX session per model. Module-level singletons in `faces.py` and `employees.py` create separate instances with separate model loads. `app.state` is the idiomatic FastAPI pattern for shared state.

### D5: CLAHE on full image before detection

**Choice**: Apply CLAHE (clipLimit=2.0, tileGridSize=(8,8)) to the full BGR image before passing to insightface, rather than on the face crop after detection.

**Rationale**: Improves face detection accuracy in low-light/backlit conditions by enhancing contrast globally. The alternative (CLAHE on crop) doesn't help detection — by then the face is already found or missed.

### D6: Keep bbox format as [x, y, w, h] for frontend compatibility

**Choice**: Convert insightface's [x1, y1, x2, y2] bbox to [x, y, w, h] before returning in API responses.

**Rationale**: The existing frontend expects [x, y, w, h]. Changing this would require frontend coordination.

## Risks / Trade-offs

- **[insightface Cython build on Windows]** → Mitigation: requires MSVC Build Tools for `mesh_core_cython`. In Docker, `gcc` is already available. Document Windows setup steps. If Cython build fails, `insightface` can be installed with `--no-build-isolation` or pre-built wheels.
- **[ buffalo_l auto-download (32MB) on first run]** → Mitigation: `entrypoint.sh` will pre-download models on container start. Docker volume caches `~/.insightface/models/`.
- **[AdaFace ONNX must be generated separately]** → Mitigation: `scripts/convert_adaface_to_onnx.py` with validation. Document the process in `MODELS.md`.
- **[All existing embeddings are invalidated]** → Mitigation: database is cleared intentionally (different model + different dtype). This is a known breaking change.
- **[ONNX model routing relies on input shape heuristics]** → Mitigation: AdaFace IR-101 uses 112×112 input (satisfies `shape ≥ 112 and shape % 16 == 0`), so insightface's `ModelRouter` correctly routes it to `ArcFaceONNX`. Verified that the model works through this path.
- **[Fallback buffalo_l recognition model (ArcFace R50) will be loaded alongside detection]** → Mitigation: Load buffalo_l for detection+alignment, then replace the recognition model with AdaFace. The ArcFace R50 weights (~30MB) are loaded but unused — acceptable overhead.