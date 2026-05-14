## ADDED Requirements

### Requirement: pytest configuration with in-memory database
The system SHALL provide a `tests/conftest.py` that configures pytest with a FastAPI `TestClient`, an in-memory SQLite database, and a valid JWT token for authenticated endpoints. The test database SHALL be created fresh for each test session.

#### Scenario: Test client with auth
- **WHEN** a test requests an authenticated endpoint
- **THEN** the test client provides a valid JWT token in the Authorization header
- **AND** the request succeeds (200 status)

#### Scenario: In-memory database isolation
- **WHEN** a test writes to the database
- **THEN** the data is available within the same test
- **AND** subsequent test sessions start with a clean database

### Requirement: Health endpoint smoke test
The system SHALL include a test that verifies the `/health` endpoint returns a successful response with the correct version field.

#### Scenario: Health check returns 200
- **WHEN** a GET request is sent to `/health`
- **THEN** the response status is 200
- **AND** the response JSON contains a `"status": "healthy"` field

### Requirement: Admin endpoint smoke test
The system SHALL include a test that verifies admin registration and login flow.

#### Scenario: Admin registration with valid invite code
- **WHEN** a POST request is sent to `/api/v1/admins/register` with valid data
- **THEN** the response status is 201 or 200
- **AND** the response contains the admin username and email

#### Scenario: Admin login returns JWT token
- **WHEN** a POST request is sent to `/api/v1/admins/login` with valid credentials
- **THEN** the response contains an `"access_token"` field

### Requirement: Face service unit tests
The system SHALL include unit tests for `FaceRecognitionService` methods: `detect_and_embed()`, `compare_faces_batch()`, and `apply_clahe()`. Tests for model-dependent methods SHALL use mocked models when real models are unavailable.

#### Scenario: CLAHE preserves image dimensions
- **WHEN** `apply_clahe()` is called on a valid BGR image
- **THEN** the output shape matches the input shape
- **AND** the output dtype is the same as input dtype

#### Scenario: Batch comparison returns correct number of results
- **WHEN** `compare_faces_batch()` is called with one query and N known embeddings
- **THEN** the result array has length N

### Requirement: Embedding serialization round-trip test
The system SHALL include tests that verify `serialize_embedding()` and `deserialize_embedding()` produce consistent results, including the legacy float64 migration path.

#### Scenario: float32 round-trip
- **WHEN** an embedding is serialized and then deserialized
- **THEN** the deserialized embedding matches the original within float32 precision

#### Scenario: float64 legacy deserialization
- **WHEN** a float64 (4096-byte) blob is deserialized
- **THEN** the result is a float32 array with the same values (within precision)