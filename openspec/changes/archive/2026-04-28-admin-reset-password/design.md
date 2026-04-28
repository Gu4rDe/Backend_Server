## Context

The face recognition backend already has an invite code system (InviteService) used for admin registration. Admins authenticate via JWT and can manage invite codes. However, there is no mechanism for an admin to reset their password if forgotten. The existing Admin model stores password_hash (bcrypt), and the AdminInviteCode model supports validation, expiration, and usage tracking.

## Goals / Non-Goals

**Goals:**
- Provide a self-service password reset flow for admins using invite code authorization
- Reuse existing InviteService.validate_invite_code() for authorization
- Reuse existing uth.hash_password() for secure password storage
- Rate-limit the endpoint to prevent abuse
- Return clear error messages for all failure modes

**Non-Goals:**
- Email-based password reset (no email service configured)
- Multi-factor recovery flows
- Password reset for employees (only admin accounts)
- Invalidating existing JWT tokens on reset

## Decisions

1. **Public endpoint (no auth required)**: The reset endpoint must be accessible without a valid JWT token since the admin has forgotten their password. Authorization is instead provided by the invite code, which acts as a one-time recovery token.

2. **Invite code consumed on success**: The invite code is marked as used only after a successful password reset, preventing reuse. This aligns with the existing invite code semantics used during registration.

3. **Username-based lookup**: The admin is identified by username (not email) since the existing login flow uses username. This is consistent with the current authentication pattern.

4. **Same password validation as registration**: The new password must meet the same constraints (min 6, max 128 chars) enforced by the existing AdminRegister schema.

5. **Rate limiting at 5/minute**: Matches the existing registration endpoint rate limit to prevent brute-force attacks on usernames or invite codes.

## Risks / Trade-offs

- **[Invite code leakage]** → If an invite code is intercepted, an attacker could reset an admin's password. Mitigation: invite codes are short-lived (configurable expiration) and single-use.
- **[No JWT invalidation]** → Existing valid tokens remain usable after password reset. Mitigation: tokens expire after 24 hours; admin can manually revoke if needed.
- **[Username enumeration]** → Different error messages for "admin not found" vs "invalid invite code" could leak valid usernames. Mitigation: use generic error messages where possible.
