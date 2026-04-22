## 1. Add onnxruntime dependency

- [x] 1.1 Add `onnxruntime>=1.16.0` to `pyproject.toml` dependencies

## 2. Migrate FaceRecognitionService to onnxruntime

- [x] 2.1 Replace `cv2.dnn.readNetFromONNX()` with `ort.InferenceSession()` in `_load_model`
- [x] 2.2 Replace `self.embedding_net.setInput()/forward()` with `session.run()` in `get_face_embedding`
- [x] 2.3 Update `model_name` and `model_status` properties to check `self.session` instead of `self.embedding_net`
- [x] 2.4 Add try/except around onnxruntime import for graceful fallback

## 3. Verify the migration

- [x] 3.1 Run `uv sync` to install the new dependency
- [x] 3.2 Restart server and confirm ArcFace model loads via onnxruntime
