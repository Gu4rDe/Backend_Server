## ADDED Requirements

### Requirement: Admin password reset via invite code
The system SHALL allow an admin to reset their password by providing their username, a valid invite code, and a new password. The endpoint SHALL be `POST /api/v1/admins/reset-password`.

#### Scenario: Successful password reset
- **WHEN** an admin submits a valid username, an unused and unexpired invite code, and a new password meeting validation requirements
- **THEN** the system updates the admin's password hash, marks the invite code as used, and returns a success message with HTTP 200

#### Scenario: Admin not found
- **WHEN** the provided username does not match any registered admin
- **THEN** the system returns HTTP 404 with an error message

#### Scenario: Invalid invite code
- **WHEN** the provided invite code does not exist, is already used, or is expired
- **THEN** the system returns HTTP 403 with an error message

#### Scenario: Invalid password format
- **WHEN** the new password is shorter than 6 characters or longer than 128 characters
- **THEN** the system returns HTTP 422 with a validation error message

#### Scenario: Rate limit exceeded
- **WHEN** more than 5 reset requests are made from the same source within one minute
- **THEN** the system returns HTTP 429 with a rate limit error

#### Scenario: Invite code consumed on success
- **WHEN** a password reset completes successfully
- **THEN** the invite code is marked as used and cannot be reused for another reset
