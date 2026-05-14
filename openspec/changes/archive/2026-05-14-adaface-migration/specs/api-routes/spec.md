## MODIFIED Requirements

### Requirement: Face recognition threshold from settings
The face recognition endpoint at `POST /api/v1/faces/recognize` SHALL use the `match_threshold` value from the `AppSettings` database table instead of a hardcoded value. If no settings record exists, the system SHALL default to `0.4`.

#### Scenario: Threshold from database settings
- **WHEN** a recognition request is made
- **AND** `AppSettings.match_threshold` is set to `0.35`
- **THEN** matches are filtered using threshold `0.35`

#### Scenario: Default threshold when no settings exist
- **WHEN** a recognition request is made
- **AND** no `AppSettings` record exists in the database
- **THEN** matches are filtered using the default threshold `0.4`

### Requirement: Singleton face service dependency injection
Both `/api/v1/faces/recognize` and `/api/v1/employees/register` SHALL receive `FaceRecognitionService` via `Depends(get_face_service)` instead of module-level instantiation. The `get_face_service` dependency SHALL retrieve the service from `request.app.state.face_service`.

#### Scenario: Recognize endpoint uses injected service
- **WHEN** a request hits `/api/v1/faces/recognize`
- **THEN** the endpoint uses the singleton `FaceRecognitionService` from `app.state`
- **AND** no separate instance is created

#### Scenario: Register endpoint uses injected service
- **WHEN** a request hits `/api/v1/employees/register`
- **THEN** the endpoint uses the same singleton `FaceRecognitionService` instance
- **AND** it is identical to the one used by the recognize endpoint

### Requirement: Bounding box format conversion
The API SHALL return face bounding boxes in `[x, y, width, height]` format for frontend compatibility. insightface's internal `[x1, y1, x2, y2]` format SHALL be converted before returning in API responses.

#### Scenario: Bbox format conversion
- **WHEN** insightface returns a face with `bbox = [x1, y1, x2, y2]`
- **THEN** the API response contains `bbox = [x1, y1, x2-x1, y2-y1]`

## REMOVED Requirements

### Requirement: Module-level FaceRecognitionService instances
**Reason**: Replaced by singleton via `app.state.face_service` and dependency injection
**Migration**: Remove `face_service = FaceRecognitionService(...)` from `faces.py` and `employees.py`; use `Depends(get_face_service)` instead

### Requirement: Direct numpy deserialization of embeddings
**Reason**: Replaced by safe `deserialize_embedding()` with size validation and dtype auto-detection
**Migration**: Replace `np.frombuffer(record.embedding, dtype=np.float64)` with `deserialize_embedding(record.embedding)`

### Requirement: Direct numpy serialization of embeddings
**Reason**: Replaced by `serialize_embedding()` that enforces float32 dtype
**Migration**: Replace `embedding.tobytes()` with `serialize_embedding(embedding)`