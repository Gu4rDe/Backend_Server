## 1. Schema Definition

- [x] 1.1 Add `AdminPasswordReset` Pydantic schema to `backend/app/schemas.py` with fields: `username` (str), `invite_code` (str, min 8, max 32), `new_password` (str, min 6, max 128)
- [x] 1.2 Add `MessageResponse` Pydantic schema to `backend/app/schemas.py` for the success response with a `message` field

## 2. Endpoint Implementation

- [x] 2.1 Add `POST /api/v1/admins/reset-password` endpoint to `backend/app/routers/admins.py`
- [x] 2.2 Implement invite code validation using `InviteService.validate_invite_code()`
- [x] 2.3 Implement admin lookup by username
- [x] 2.4 Implement password hash update using `auth.hash_password()`
- [x] 2.5 Mark invite code as used using `InviteService.mark_as_used()`
- [x] 2.6 Add rate limiting at 5/minute using `@limiter.limit("5/minute")`

## 3. Error Handling

- [x] 3.1 Return HTTP 404 when admin username is not found
- [x] 3.2 Return HTTP 403 when invite code is invalid, expired, or already used
- [x] 3.3 Return HTTP 422 for password validation failures (handled by Pydantic schema)

## 4. Verification

- [x] 4.1 Test successful password reset flow end-to-end
- [x] 4.2 Test that used invite codes cannot reset passwords again
- [x] 4.3 Test that expired invite codes are rejected
- [x] 4.4 Test rate limiting behavior
