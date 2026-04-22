## ADDED Requirements

### Requirement: ONNX runtime model loading
The `FaceRecognitionService` SHALL use `onnxruntime.InferenceSession` to load the ArcFace ONNX model instead of OpenCV's `cv2.dnn.readNetFromONNX()`.

#### Scenario: Model loads successfully via onnxruntime
- **WHEN** the ArcFace ONNX model file exists and is valid
- **THEN** `onnxruntime.InferenceSession` is created with `CPUExecutionProvider` and the session is stored

#### Scenario: Model file does not exist
- **WHEN** the ONNX model file is missing at the expected path
- **THEN** the service attempts to download it from the configured URL

#### Scenario: Model download succeeds but load fails
- **WHEN** the model is downloaded but `InferenceSession` creation fails
- **THEN** a warning is printed and the service falls back to histogram mode

#### Scenario: onnxruntime is not installed
- **WHEN** `import onnxruntime` raises `ImportError`
- **THEN** the service falls back to histogram mode without error

### Requirement: ONNX runtime inference
The `get_face_embedding` method SHALL use the onnxruntime session for inference when available.

#### Scenario: Embedding extracted via onnxruntime
- **WHEN** `session` is not None and a valid face image is provided
- **THEN** the image is preprocessed (112x112, BGR→RGB, normalized) and passed through `session.run()` to produce a 512-dim embedding

#### Scenario: Embedding extracted via histogram fallback
- **WHEN** `session` is None
- **THEN** the histogram fallback method (96x96 grayscale, 64-bin histogram, padded to 512-dim) is used

### Requirement: onnxruntime dependency
The project SHALL include `onnxruntime>=1.16.0` as a dependency in `pyproject.toml`.

#### Scenario: Dependency is declared
- **WHEN** `pyproject.toml` is read
- **THEN** `onnxruntime>=1.16.0` is listed in the project dependencies
