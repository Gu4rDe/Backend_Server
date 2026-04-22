## Why

OpenCV's `cv2.dnn.readNetFromONNX()` cannot parse the ArcFace ONNX model due to unsupported operators (e.g., `InstanceNormalization`, `Resize`). This causes the model to always fail loading, forcing the server into the histogram fallback mode which provides poor recognition accuracy. The fallback was designed as a safety net, not as the primary recognition engine.

## What Changes

- Replace OpenCV DNN inference with `onnxruntime` for ArcFace model loading and inference
- Add `onnxruntime>=1.16.0` as a project dependency
- Keep the histogram fallback as a safety net if onnxruntime is unavailable or the model fails to load
- No API changes — the `FaceRecognitionService` public interface (`detect_faces`, `get_face_embedding`, `compare_faces`, `compare_faces_batch`) remains unchanged

## Capabilities

### New Capabilities
- `onnxruntime-inference`: Uses onnxruntime for ArcFace model inference instead of OpenCV DNN, with full ONNX operator support

### Modified Capabilities
<!-- No existing capabilities are modified -->

## Impact

- `backend/pyproject.toml` — new dependency
- `backend/app/services/face_service.py` — model loading and inference logic
- No API contract changes, no database changes, no breaking changes
