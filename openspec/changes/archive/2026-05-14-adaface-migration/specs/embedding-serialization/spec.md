## ADDED Requirements

### Requirement: float32 embedding storage
All embeddings SHALL be stored as `np.float32` (4 bytes per element, 2048 bytes per 512-dim embedding). The system SHALL NOT store embeddings as `np.float64`.

#### Scenario: Serialize embedding to database
- **WHEN** an embedding is saved to the database
- **THEN** it is first cast to `np.float32` (if not already) and serialized via `.tobytes()`
- **AND** the resulting byte array is exactly 2048 bytes long

#### Scenario: Deserialize float32 embedding from database
- **WHEN** a 2048-byte blob is read from the database
- **THEN** `deserialize_embedding()` returns a `np.float32` array of shape (512,)
- **AND** the array is a copy (not a view of the buffer)

### Requirement: Legacy float64 deserialization
The `deserialize_embedding()` function SHALL detect and convert legacy `np.float64` embeddings (4096 bytes) to `np.float32`. This enables reading old data during a transition period, though the database will be cleared in this migration.

#### Scenario: Deserialize float64 legacy embedding
- **WHEN** a 4096-byte blob is read from the database
- **THEN** `deserialize_embedding()` interprets it as `np.float64`, converts to `np.float32`, and returns a shape (512,) array
- **AND** the conversion preserves values within float32 precision

#### Scenario: Invalid embedding size
- **WHEN** a blob of any size other than 2048 or 4096 bytes is read
- **THEN** `deserialize_embedding()` raises `ValueError` with a message indicating the invalid size

### Requirement: Embedding validation helper
The system SHALL provide a `validate_embedding(data: bytes) -> bool` function that returns `True` if `len(data)` is 2048 or 4096, and `False` otherwise.

#### Scenario: Valid float32 embedding
- **WHEN** `validate_embedding()` is called with 2048 bytes
- **THEN** it returns `True`

#### Scenario: Valid float64 legacy embedding
- **WHEN** `validate_embedding()` is called with 4096 bytes
- **THEN** it returns `True`

#### Scenario: Invalid embedding size
- **WHEN** `validate_embedding()` is called with any other number of bytes
- **THEN** it returns `False`

### Requirement: Employee embedding column nullable
The `Employee.embedding` column SHALL be `nullable=True` (LargeBinary). This allows employees to exist without face embeddings temporarily.

#### Scenario: Create employee without embedding
- **WHEN** an employee is created without providing a face photo
- **THEN** the `embedding` column is stored as NULL
- **AND** the record is valid in the database

#### Scenario: Create employee with embedding
- **WHEN** an employee is created with a face photo
- **THEN** the `embedding` column is stored as a 2048-byte float32 blob