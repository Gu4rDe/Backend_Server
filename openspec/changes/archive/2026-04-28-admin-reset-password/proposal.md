## Why

Admins who forget their passwords currently have no self-service recovery mechanism. This change adds a password reset endpoint that uses the existing invite code system to authorize resets, allowing admins to recover access without requiring another admin's intervention.

## What Changes

- New `POST /api/v1/admins/reset-password` endpoint accepting `{username, invite_code, new_password}`
- Validates the invite code using the existing `InviteService.validate_invite_code()`
- Updates the admin's password hash in the database
- Marks the invite code as used after successful reset
- Returns a success message on completion
- Rate-limited to prevent brute-force attacks

## Capabilities

### New Capabilities

- `admin-password-reset`: Password reset for admin accounts via invite code authorization

### Modified Capabilities

<!-- No existing capabilities are modified -->

## Impact

- **New endpoint**: `POST /api/v1/admins/reset-password` in `backend/app/routers/admins.py`
- **New Pydantic schema**: `AdminPasswordReset` in `backend/app/schemas.py`
- **No database changes**: Uses existing `Admin` and `AdminInviteCode` models
- **No new dependencies**: Reuses existing `InviteService` and `auth.hash_password`
