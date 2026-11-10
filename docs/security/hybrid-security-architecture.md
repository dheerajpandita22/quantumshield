# QuantumShield — Hybrid Cybersecurity Architecture & Threat Model

## 1. Responsibility split

> **Rule:** quantum-assisted verification is an *experimental additional layer*. Every conventional attack class below is stopped (or not) by **conventional** controls. Nothing in this document claims that quantum teleportation prevents SQL injection, XSS, session theft, or network attacks.

| Quantum-assisted (experimental layer) | Conventional (the actual security boundary) |
|---|---|
| Quantum verification evidence (QVE) generation and statistical checking | Authentication (passwords, TOTP, machine HMAC keys) |
| Channel-anomaly evaluation of the *simulated* quantum link | Authorization (RBAC, RLS, scopes) |
| Detection of controlled perturbations (tamper library) | Web-app security (CSP, CSRF, output encoding) |
| Bell/teleportation fidelity checks of the simulated channel | Database security (roles, parameterised SQL, RLS, encryption) |
| Statistical verification of expected quantum behaviour | Session security, rate limiting, input validation |
| — | Replay protection (nonce + timestamp), request integrity (HMAC) |
| — | TLS, network isolation, secrets management, audit logging |

Decision rule (see Quantum spec §9.5): `final = classical_ok AND quantum_ok`; quantum can add a rejection, never remove one.

## 2. Authentication

### 2.1 Human users (Defender and Lab)
- Passwords: **Argon2id** (target ≥ 64 MiB, t=3, p=1, tuned to ~250 ms; never below OWASP minimums m=19 MiB, t=2). Per-user random salt. Optional pepper from secret manager.
- Password policy: ≥ 12 chars, breach-list check (k-anonymity API or local list), no composition rules theatre.
- MFA: TOTP (RFC 6238) MUST be available; REQUIRED for `admin`, recommended for others.
- Login throttling: 5 failures / 15 min per (account, IP) → exponential delay; 20 / min per IP; uniform error message and timing for "unknown user" vs "wrong password".
- Account recovery is out of scope for v1 (admin reset only); no email enumeration.

### 2.2 Machine identities
| Identity | Credential | Scope |
|---|---|---|
| Protected app (sandbox target or customer app) | `key_id` + 256-bit HMAC secret (per resource) | `ingest:write` for that resource only |
| Attack runner | service JWT (EdDSA, 15 min, `aud=lab-runner`, `scope=lab:run`, `sub=run_id`) minted by the API when a run starts | execute steps of **one** run; ingest only for registered sandbox links |
| Quantum worker | DB/Redis roles (`qs_worker`) | read job payload, write results |

## 3. Authorization (RBAC)

Roles: `admin`, `security_analyst`, `viewer`, `lab_operator`, `lab_viewer`, `auditor`. Roles are per-organisation.

| Permission | admin | security_analyst | viewer | lab_operator | lab_viewer | auditor |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `resources:read` | ✓ | ✓ | ✓ | | | ✓ |
| `resources:write` | ✓ | | | | | |
| `events:read` | ✓ | ✓ | ✓ | | | ✓ |
| `incidents:read` | ✓ | ✓ | ✓ | | | ✓ |
| `incidents:write` | ✓ | ✓ | | | | |
| `responses:execute` (manual) | ✓ | ✓ | | | | |
| `quantum:read` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `quantum:calibrate` | ✓ | ✓ | | | | |
| `lab:targets:write` | ✓ | | | ✓ | | |
| `lab:runs:execute` | ✓ | | | ✓ | | |
| `lab:runs:read` | ✓ | ✓ | | ✓ | ✓ | ✓ |
| `reports:read` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `reports:create` | ✓ | ✓ | | ✓ | | |
| `ground_truth:read` | (evaluation service only; **no human role**) |
| `audit:read` | ✓ | | | | | ✓ |
| `users:write` | ✓ | | | | | |

Enforcement: FastAPI dependency per route (`Depends(require_perm("incidents:write"))`) **and** PostgreSQL RLS (`org_id = current_setting('app.org_id')::uuid`). IDOR prevention: all object lookups are `WHERE id = :id AND org_id = :org` — never by id alone. A negative test per route with a different-org user MUST return `404`.

## 4. Sessions, cookies, CSRF

- Server-side session rows (`sessions` table; opaque 256-bit id stored hashed with SHA-256). No JWT for browser sessions.
- Cookie: `__Host-qs_def_sid` (Defender) / `__Host-qs_lab_sid` (Lab); `HttpOnly; Secure; SameSite=Lax; Path=/` (host-only, issued by the API host). The API maps cookie name ⇄ allowed `Origin`; a Lab cookie presented from the Defender origin is rejected.
- Idle timeout 30 min; absolute timeout 8 h; rotation at login, MFA completion, and role change; logout revokes server-side.
- **CSRF** (cookies are ambient credentials): use a session-bound synchronizer token, not a JavaScript-readable cookie. Return `csrf_token` in the JSON body of `POST /auth/login` and `GET /auth/me`; keep it in frontend memory only and send it as `X-CSRF-Token` on every state-changing browser request. The API validates the token against the active session using a server-held HMAC secret and constant-time comparison. Also require an exact allowlisted `Origin` on every state-changing browser request. Do not set a `qs_csrf` cookie. `SameSite=Lax` is defence in depth only because `defender.`, `lab.`, `api.` are same-site.
- Machine-to-machine calls use signature auth, not cookies; CSRF does not apply and cookies are ignored on `/ingest`.
- WebSocket: Origin check + single-use ticket (Architecture §9).

## 5. Request integrity, freshness and replay prevention

### 5.1 Signed request format (machine → `/ingest/*`, `/lab/*` runner calls)

Headers:

| Header | Content |
|---|---|
| `X-QS-Key-Id` | public key id (uuid) |
| `X-QS-Timestamp` | Unix epoch **milliseconds**, UTC |
| `X-QS-Nonce` | 16–32 random bytes, base64url without padding (22–43 chars) |
| `X-QS-Body-SHA256` | hex SHA-256 of raw body (empty body = hash of empty string) |
| `X-QS-Signature` | `base64url(HMAC-SHA256(secret, canonical))` |

Canonical string (UTF-8, `\n` separated, no trailing newline):

```
QS1\n
{METHOD upper}\n
{path, as received, percent-encoding normalised}\n
{query, sorted by key then value, re-encoded}\n
{key_id}\n
{timestamp}\n
{nonce}\n
{body_sha256}
```

Server algorithm (order matters; cheap checks first, all failures produce an event):

1. Parse and bound header sizes; reject if any header missing → `signature.invalid`.
2. Look up `key_id` (cache ≤ 60 s); unknown/revoked/expired → `identity.unknown_key`.
3. `|now − timestamp| ≤ 60 s` else `request.stale` (also rejects future-dated).
4. Recompute body hash from the raw bytes; mismatch → `signature.invalid`.
5. Recompute HMAC; compare with `hmac.compare_digest`; mismatch → `signature.invalid`.
6. **Atomically** claim nonce: `SET qs:nonce:{key_id}:{nonce} 1 NX EX 300`. Failure ⇒ `replay.detected`. (Only *after* signature verification, so unauthenticated floods cannot fill the nonce cache.)
7. Persist `(key_id, nonce, ts)` in `request_nonces` (unique) for audit; unique violation ⇒ `replay.detected` (belt and braces if Redis was flushed).
8. Proceed to QVE (Quantum spec §9) and detection.

**Nonce TTL rule:** TTL (300 s) ≥ 2 × skew window (120 s) + margin. If Redis is unavailable or flushed, requests with timestamps older than the Redis recovery time are rejected (store `redis_epoch`, ignore nonce-cache for older timestamps → fail closed).

**Duplicate detection summary**
| Replay variant | Caught by |
|---|---|
| Exact same signed request within 60 s | nonce claim |
| Same request after 60 s | timestamp skew |
| Same request with new nonce but old signature | HMAC mismatch |
| Same body, new valid signature (legit re-send) | accepted as new request; business-level idempotency is the app's job |
| Replayed QVE with a new request | `params_digest` mismatch (bound to request digest and nonce) |
| Replayed QVE with the same request | nonce claim + `evidence_digest` uniqueness |
| Session replay across IPs/UA | session binding anomaly rule (detection §R-SESS) |

### 5.2 Secret storage
$K_{req}$, $K_q$ are stored with envelope encryption (AES-256-GCM, per-record DEK, KEK from KMS / secret manager; local dev KEK from env var `QS_DEV_KEK`). Secrets are shown **once** on creation. Rotation: two active keys per resource for an overlap window; `key_id` embedded in the signature header selects the key.

## 6. Rate limiting and abuse control

Token buckets in Redis (Lua for atomicity). Keys include org and principal.

| Endpoint class | Key | Limit | On exceed |
|---|---|---|---|
| `POST /auth/login` | IP, and account | 20/min/IP; 5/15 min/account | 429 + `ratelimit.exceeded` + delay |
| `/ingest/*` | `key_id` | 600/min, burst 100 | 429, event, optional `THROTTLE` response |
| Quantum job submission | org | 60/min; ≤ 200 queued; ≤ 200 000 shots/job | 429 / 422 |
| Lab runs | org | 10 concurrent runs; each run has request-per-second cap from the scenario | 429 |
| Read APIs | session | 300/min | 429 |
| WebSocket tickets | session | 10/min | 429 |

Return `Retry-After`. Rate-limit failure of the limiter backend ⇒ **fail closed** for auth and ingest, fail open (with metric) for read-only dashboards.

## 7. Input validation and injection defences

- **Pydantic v2 strict models**, `extra="forbid"`, explicit max lengths, enums for categorical fields, `Decimal`/bounded floats for quantum parameters (e.g., `0 ≤ θ ≤ π`, `shots ≤ 200000`).
- Body limit 1 MiB (`413`), JSON only, `Content-Type` enforced, depth limit 10.
- **SQL injection:** SQLAlchemy Core/ORM with bound parameters only; static analysis rule (Semgrep) bans f-strings/`%`/`+` in `text()` and `execute()`; DB role `qs_api` has no DDL, no `COPY PROGRAM`, no superuser; `statement_timeout = 5s`.
- **XSS:** React escaping by default; ban `dangerouslySetInnerHTML` (ESLint rule); event payloads and attacker-controlled strings (e.g., User-Agent, sandbox form input captured in events) are rendered as text only and length-capped on display; CSP: `default-src 'self'; script-src 'self' 'nonce-{per-request}' ; style-src 'self' 'unsafe-inline'` (Tailwind) `; connect-src 'self' https://api.<domain> wss://api.<domain>; frame-ancestors 'none'; base-uri 'none'; object-src 'none'`; plus `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` minimal, HSTS `max-age=31536000; includeSubDomains`.
- **SSRF** on lab target registration: URL scheme allowlist (`https`/`http` for internal sandbox), resolve DNS server-side, reject loopback/link-local/metadata (169.254.169.254) unless the target is a registered sandbox network, re-resolve at attack time (anti-DNS-rebinding), pin IP.
- **Path/command injection:** no shell invocation with user data; no file paths from users.
- **Deserialization:** JSON only; no pickle anywhere (Celery serializer = json).
- **Mass assignment:** response/request models are distinct from ORM models.

## 8. Audit logging

- Table `audit_log` (append-only): `id, ts, actor_type, actor_id, org_id, action, object_type, object_id, ip, user_agent, outcome, details jsonb, prev_hash, hash`.
- `hash = SHA256(prev_hash || canonical_json(row without hash))` → tamper-evident chain (per org). `UPDATE/DELETE/TRUNCATE` revoked for all app roles; insert via `SECURITY DEFINER` function.
- Audited: logins, failures, MFA, role changes, resource/target registration, key issue/rotate/revoke, response actions (auto and manual), incident status changes, lab run start/cancel, report creation, configuration changes, safety violations.
- Daily export of the latest chain head to object storage (immutable bucket) as external anchor.
- Logs never contain secrets, session ids, full tokens, nonce+signature pairs, or password material (log-redaction filter + unit test).

## 9. Data isolation and secrets management

- Multi-tenant column `org_id` everywhere + RLS; app sets `SET LOCAL app.org_id` per transaction. Evaluation uses role `qs_eval` with explicit grants.
- Lab data in schema `lab`; **synthetic data only** (generator in `sandbox/`), no production data imports; a CI check forbids committing real-looking PII fixtures.
- Backups: encrypted; no restore of prod data to dev.
- Secrets: never in repo; `.env.example` lists names; production secrets in the platform secret manager; startup fails if a required secret is missing or equals a known-dev default; secret scanning (gitleaks) in CI and pre-commit.

## 10. Secure API communication
TLS ≥ 1.2 (prefer 1.3); HSTS; CORS exact origins, `Access-Control-Allow-Credentials: true` only for those origins; no wildcard. Internal links (API↔Postgres/Redis) over private network with TLS. Service-to-service `Authorization` as in §2.2. API versioning `/api/v1`; errors in RFC 9457 `application/problem+json` with no stack traces or SQL text.

---

## 11. Threat model

Attacker capability legend: **A0** unauthenticated remote; **A1** holds a valid low-privilege session; **A2** can observe/modify traffic in the *simulated* quantum channel; **A3** holds a stolen `key_id` only; **A4** holds stolen secret; **A5** insider with DB read access.

| ID | Threat | Attack surface | Attacker | Potential impact | Detection | Mitigation | Residual risk |
|---|---|---|---|---|---|---|---|
| T1 | Credential stuffing / brute force | `/auth/login` | A0 | Account takeover | Failure-rate rule R-AUTH-1 | Argon2id, throttle, MFA, breach list | Low (MFA-less user with leaked password) |
| T2 | Session hijack / fixation | Cookie, XSS, network | A0/A1 | Operator impersonation | Session-binding anomaly R-SESS-1 | HttpOnly, Secure, `__Host-`, rotation, short TTL | Medium if XSS present |
| T3 | CSRF | State-changing routes | A0 via victim browser | Unauthorised response actions | Origin/CSRF mismatch events | Origin check + session-bound synchronizer token | Low |
| T4 | Stored XSS via event payloads | UI event stream | A0 (via sandbox/ingest data) | Session theft | Pattern rule R-XSS-1, CSP violation reports | Output encoding, CSP nonce, no `innerHTML` | Low–medium |
| T5 | SQL injection | API params, sandbox app | A0/A1 | Data theft/destruction | R-SQLI-1 patterns + DB error spike | Parameterised queries, least-privilege role, RLS | Low (platform); **sandbox app intentionally vulnerable** |
| T6 | Replay of signed request | `/ingest` | A2/A0 (captured) | Duplicate action / bypass | Nonce collision, stale ts | Nonce + timestamp + HMAC | Low; Redis loss window mitigated by DB nonce table |
| T7 | Replay of QVE | QVE submission | A0 w/ capture | Pass verification without fresh quantum evidence | Digest uniqueness, params mismatch | Request-bound HKDF, MAC, digest unique | Low |
| T8 | Forged QVE (no key) | QVE API | A0 | Impersonate verification | MAC invalid, params_digest mismatch | HMAC under $K_q$ | Low (computational) |
| T9 | Impersonation with only `key_id` | `/ingest` | A3 | Pose as another identity | Signature invalid; identity.mismatch | Secret never transmitted; HMAC | Low |
| T10 | Impersonation with stolen secret | `/ingest` | A4 | Full impersonation | Anomalous source/behaviour R-BEH-1 | Rotation, per-resource keys, IP allowlist optional | **High if secret stolen** (no quantum fix in simulation) |
| T11 | Quantum-channel manipulation | Simulated link | A2 | Undetected state tamper | χ² + structure analysis (Quantum §8) | Multi-basis (θ,φ) settings, calibration | Noise-mimicking attacker within $\kappa_{\min}$ (T12) |
| T12 | Noise-mimicking / within-budget attacker | Simulated link | A2 | Evades detection | None by design | Tight $\kappa_{\min}$, report noise budget | **Accepted and documented** |
| T13 | Calibration poisoning | Calibration jobs | A1 with `quantum:calibrate` or A2 during calibration | Verifier tolerant to attack | Over-dispersion check, drift alarm, comparison to previous calibration | Role limits, calibrate only from trusted channel profile, require 2 consecutive windows, store immutably | Medium |
| T14 | API/job flooding (DoS) | Ingest, job submit | A0/A1 | Queue exhaustion, delayed verification | Rate metrics, queue depth | Rate limits, queue caps, shot budgets, autoscale | Medium |
| T15 | Cross-tenant access (IDOR) | Object endpoints | A1 | Data leak | AuthZ-denied events, tests | org-scoped queries + RLS | Low |
| T16 | Attack Lab escapes sandbox (third-party/prod targeting) | Attack runner egress | misuse / bug | Legal/ethical harm | `lab.safety.violation`, egress firewall logs | Signed target registry, egress allowlist, double check in API and runner, rate caps, kill switch | Low with network enforcement; **must be network-enforced, not just code** |
| T17 | Ground-truth leakage | DB, code | developer error | Inflated detection metrics | Permission tests | Separate table/role, no FK from detections | Low |
| T18 | Audit log tampering | DB | A5 | Loss of accountability | Hash-chain verification job | Append-only, revoked privileges, external anchor | Low–medium (DBA) |
| T19 | Secret leakage via logs/errors | Logging | A5/A0 | Key compromise | Log scanners | Redaction, no secrets in exceptions, secret scanning | Low |
| T20 | Cross-site WebSocket hijack | WS endpoint | A0 via victim browser | Live data exfil | Origin mismatch events | Origin check + one-time ticket | Low |
| T21 | Dependency/supply-chain compromise | pip/npm, Qiskit | A0 | RCE | SCA alerts | Lockfiles, hash pinning, Dependabot, minimal base images | Medium |
| T22 | SSRF via target registration | `/lab/targets` | A1 lab_operator | Internal network scan | Registration validation events | Scheme/IP allowlists, DNS pinning | Low |
| T23 | Mislabelling simulation as hardware | Reports/UI | developer/analyst | Scientific misrepresentation | DB CHECK, schema tests | Provenance invariants (Quantum §10) | Low |
| T24 | Brute-force/guess QVE parameters | QVE API | A0 | Forgery | Repeated MAC failures | MAC under secret; rate limit | Negligible |

## 12. Acceptance criteria

| ID | Criterion |
|---|---|
| SEC-1 | Signed-request test vectors (published in `docs/api`) verify in both client helper and server; any single-byte change to method, path, query, body, timestamp or nonce fails. |
| SEC-2 | Replaying an identical valid request within 60 s yields `replay.detected` and HTTP 200 with `classical: REJECT` (never `ACCEPT`). |
| SEC-3 | Flushing Redis then replaying a request from before the flush is rejected. |
| SEC-4 | A user of org A requesting an object of org B receives `404` on every object route (parametrised test over all routes). |
| SEC-5 | CSRF: state-changing request without `X-CSRF-Token` or with wrong `Origin` returns 403 for every mutating route. |
| SEC-6 | No route returns stack traces/SQL text; verified by fuzzing 500 malformed payloads per route. |
| SEC-7 | Semgrep rule set (SQL concat, `eval`, `pickle`, `shell=True`) passes with zero findings in `backend/`. |
| SEC-8 | CSP present on every HTML response of both frontends; no inline script without nonce (browser test). |
| SEC-9 | Audit chain verification job passes after the integration test suite and fails when a row is manually altered. |
| SEC-10 | Secrets scan clean; app refuses to start in `prod` with dev KEK. |
| SEC-11 | Rate-limit tests demonstrate 429 + `Retry-After` for login, ingest, job submission. |
| SEC-12 | Documentation (README + UI "About" page) contains the statements of §1 and Quantum §11 verbatim. |
