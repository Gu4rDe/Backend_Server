## ADDED Requirements

### Requirement: Model status property
The `FaceRecognitionService` SHALL expose a `model_name` property that returns the name of the active recognition engine.

#### Scenario: ArcFace ONNX is loaded
- **WHEN** the ArcFace ONNX model was successfully loaded or downloaded
- **THEN** `model_name` returns `"arcface_onnx"`

#### Scenario: Fallback histogram mode is active
- **WHEN** the ArcFace ONNX model failed to load and no download was available
- **THEN** `model_name` returns `"histogram_fallback"`

### Requirement: Startup model status logging
The server SHALL log the active face recognition model during startup via the structured logger in the lifespan function.

#### Scenario: Server starts with ArcFace ONNX
- **WHEN** the server starts and ArcFace ONNX model is active
- **THEN** a log message at INFO level indicates `"Face recognition model: arcface_onnx"`

#### Scenario: Server starts with fallback mode
- **WHEN** the server starts and histogram fallback is active
- **THEN** a log message at INFO level indicates `"Face recognition model: histogram_fallback"`
