# ADR-FE-001: CSRF token transport for browser applications

- **Status:** Accepted for MVP
- **Date:** 2026-11-10
- **Decision owners:** QuantumShield architecture team

## Context

The Defender and Attack Lab frontends run on separate application origins from the API. The API issues host-only `__Host-` HttpOnly session cookies. JavaScript running on either frontend cannot read a host-only cookie scoped to the API host. A JavaScript-readable double-submit cookie would therefore be unavailable to the frontend and would create avoidable cross-origin cookie complexity.

## Decision

Use a session-bound synchronizer token:

1. `POST /api/v1/auth/login` and `GET /api/v1/auth/me` return `csrf_token` in their JSON response.
2. The frontend stores the token in application memory only. Do not place it in localStorage, sessionStorage, IndexedDB, URLs, or a JavaScript-readable cookie.
3. The API client sends `X-CSRF-Token` on every state-changing browser request.
4. The API validates the token against the active server-side session using a server-held HMAC secret and constant-time comparison.
5. The API also requires an exact allowlisted `Origin` for every state-changing browser request.
6. No `qs_csrf` cookie is set.
7. Machine-to-machine HMAC-authenticated requests do not use browser CSRF tokens.

## Consequences

- The frontend must re-fetch `/auth/me` after a page reload to obtain a fresh in-memory CSRF token.
- On logout or session expiry, clear the in-memory token.
- Cross-origin credentialed requests require narrowly scoped CORS origins and credentials; wildcard origins are prohibited.
- Tests must verify missing, incorrect, expired/session-mismatched CSRF tokens and disallowed origins all fail closed with 403.

## Required tests

- Login returns a CSRF token and sets only the HttpOnly session cookie.
- `/auth/me` returns the active session's CSRF token.
- A valid token plus allowed Origin permits a mutating request.
- Missing/invalid token or disallowed/missing Origin rejects a mutating request.
- No CSRF token appears in browser storage or cookies.
