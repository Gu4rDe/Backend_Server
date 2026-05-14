## 1. Add model_name property to FaceRecognitionService

- [x] 1.1 Add `model_name` property to `FaceRecognitionService` that returns `"arcface_onnx"` or `"histogram_fallback"` based on `embedding_net` state

## 2. Log model status during server startup

- [x] 2.1 Import `FaceRecognitionService` instance from `faces.py` in `main.py` lifespan function
- [x] 2.2 Add INFO-level log message in lifespan showing active model name
