## ADDED Requirements

### Requirement: Singleton FaceRecognitionService instance
The system SHALL initialize exactly one `FaceRecognitionService` instance during application startup (in the `lifespan` handler) and store it on `app.state.face_service`. All routers SHALL access the service via `Depends(get_face_service)` dependency injection. The system SHALL NOT create module-level instances of `FaceRecognitionService`.

#### Scenario: Service initialized once at startup
- **WHEN** the FastAPI application starts
- **THEN** exactly one `FaceRecognitionService` instance is created and stored on `app.state.face_service`
- **AND** a log message with model status is emitted

#### Scenario: Routers share single instance
- **WHEN** multiple routers call `Depends(get_face_service)`
- **THEN** they receive the same `FaceRecognitionService` object (identity check passes)

### Requirement: insightface detection with alignment
The system SHALL use insightface `FaceAnalysis` with the `buffalo_l` model pack for face detection. The detector SHALL produce bounding boxes and 5-point facial landmarks. Face alignment SHALL be performed automatically via insightface's `norm_crop` using a similarity transform from detected keypoints.

#### Scenario: Detect faces in an image
- **WHEN** an image is passed to `detect_and_embed()`
- **THEN** the system detects faces using SCRFD with confidence filtering
- **AND** each detected face includes bounding box, 5 keypoints, and aligned face crop

#### Scenario: Face alignment is automatic
- **WHEN** insightface processes a face with detected keypoints
- **THEN** the face is aligned via `norm_crop` (5-point similarity transform to 112×112 reference points) before embedding extraction
- **AND** no separate alignment step is needed in application code

### Requirement: AdaFace IR-101 recognition model
The system SHALL use AdaFace IR-101 (converted to ONNX) as the recognition model. The model SHALL be loaded by replacing insightface's default recognition model after `FaceAnalysis` initialization. The system SHALL produce 512-dimensional float32 L2-normalized embeddings.

#### Scenario: AdaFace model loaded successfully
- **WHEN** `FaceRecognitionService` initializes
- **THEN** the AdaFace IR-101 ONNX model is loaded as the recognition model
- **AND** `model_status` reports "insightface SCRFD + AdaFace IR-101"

#### Scenario: Embedding extraction produces correct output
- **WHEN** a face is processed through the recognition pipeline
- **THEN** the output embedding is a numpy array of shape (512,) with dtype float32
- **AND** the embedding is L2-normalized (norm ≈ 1.0)

### Requirement: CLAHE preprocessing
The system SHALL apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to the full BGR image before face detection. Parameters SHALL be `clipLimit=2.0` and `tileGridSize=(8, 8)`. The CLAHE SHALL be applied to the L channel in LAB color space.

#### Scenario: CLAHE enhances low-light image
- **WHEN** a low-light or backlit image is processed
- **THEN** CLAHE is applied to the full image before detection
- **AND** the output image dimensions match the input dimensions

#### Scenario: CLAHE is idempotent on well-lit images
- **WHEN** a well-lit image is processed
- **THEN** CLAHE does not corrupt or distort the image
- **AND** face detection still works correctly

### Requirement: detect_and_embed API
The system SHALL provide a `detect_and_embed(image, conf_threshold=0.5)` method that performs the full pipeline: CLAHE → detection → alignment → embedding extraction. It SHALL return a list of `FaceResult` objects, each containing `bbox` (x, y, w, h), `embedding` (float32 ndarray), and `confidence` (float).

#### Scenario: Multiple faces detected
- **WHEN** an image contains multiple faces above the confidence threshold
- **THEN** `detect_and_embed` returns a `FaceResult` for each detected face
- **AND** each result contains a valid bbox, embedding, and confidence score

#### Scenario: No faces detected
- **WHEN** an image contains no detectable faces
- **THEN** `detect_and_embed` returns an empty list

#### Scenario: Faces below confidence threshold
- **WHEN** a face is detected but its confidence is below `conf_threshold`
- **THEN** that face is excluded from results

### Requirement: compare_faces_batch comparison
The system SHALL provide a `compare_faces_batch(query_embedding, known_embeddings)` method that computes cosine similarity via matrix-vector multiplication. Threshold filtering SHALL be performed by the caller, not by this method.

#### Scenario: Batch comparison produces correct similarities
- **WHEN** a query embedding and a matrix of known embeddings are provided
- **THEN** the method returns an array of similarity scores (one per known embedding)
- **AND** scores are computed as `known_embeddings @ query_embedding`

### Requirement: No fallback recognition
The system SHALL NOT include histogram-based or any other fallback recognition method. If the insightface or AdaFace model fails to load, the service SHALL raise a `RuntimeError` during initialization.

#### Scenario: Model fails to load
- **WHEN** insightface or the AdaFace ONNX model cannot be loaded at startup
- **THEN** a `RuntimeError` is raised
- **AND** the application fails to start (no degraded mode)

## REMOVED Requirements

### Requirement: MediaPipe face detection
**Reason**: Replaced by insightface SCRFD detector (better accuracy, landmarks included)
**Migration**: All detection calls now use insightface `FaceAnalysis.get()`

### Requirement: ArcFace ONNX direct loading
**Reason**: Replaced by AdaFace IR-101 loaded through insightface's model zoo
**Migration**: `download_model()` and `_load_model()` removed; model loading is handled by insightface + custom ONNX path

### Requirement: Histogram fallback recognition
**Reason**: Production-only system; fallback produces unusable embeddings
**Migration**: No migration needed; histogram code is deleted entirely

### Requirement: Module-level FaceRecognitionService instantiation
**Reason**: Dual instantiation wastes memory; singleton pattern via app.state is idiomatic FastAPI
**Migration**: Routers use `Depends(get_face_service)` instead of creating their own instance