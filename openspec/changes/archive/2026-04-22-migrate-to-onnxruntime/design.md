## Context

The `FaceRecognitionService` currently uses `cv2.dnn.readNetFromONNX()` to load the ArcFace model. This fails at runtime with "Unsupported format or combination of formats" because OpenCV's ONNX importer does not support all ONNX operators used by the ArcFace model. As a result, the server always falls back to histogram-based recognition, which is significantly less accurate.

Two modules create separate `FaceRecognitionService` instances: `faces.py` and `employees.py`. Each independently loads the model.

## Goals / Non-Goals

**Goals:**
- ArcFace model loads and runs successfully using onnxruntime
- Histogram fallback preserved for resilience if onnxruntime fails
- Public API of `FaceRecognitionService` unchanged — consumers need no modifications

**Non-Goals:**
- No GPU support (CPU only via `CPUExecutionProvider`)
- No changes to face detection (still MediaPipe)
- No changes to embedding comparison logic
- No model retraining or architecture changes

## Decisions

1. **Use `onnxruntime` (CPU) not `onnxruntime-gpu`**: Simpler dependency, no CUDA requirements. GPU can be added later if needed.

2. **Rename `self.embedding_net` → `self.session`**: Reflects the onnxruntime naming. The `model_name` and `model_status` properties check `self.session is not None`.

3. **Capture input name at load time**: `self._input_name = session.get_inputs()[0].name` — avoids hardcoding input names and makes the code resilient to model variations.

4. **Keep two singleton instances**: Both `faces.py` and `employees.py` create their own `FaceRecognitionService`. Each loads its own onnxruntime session (~130MB). This is acceptable for now; deduplication could be a future optimization.

5. **Error handling**: Wrap `ort.InferenceSession()` in try/except. On failure, log warning and fall through to histogram mode — same pattern as before.

## Risks / Trade-offs

- **[Dependency size]** onnxruntime adds ~50MB → Mitigation: acceptable for server deployment; already using heavy deps like opencv and mediapipe
- **[Two instances = 260MB memory]** → Mitigation: future deduplication via shared service, not in scope
- **[onnxruntime import failure]** → Mitigation: import wrapped in try/except, fallback activates
