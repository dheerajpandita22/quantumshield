# QuantumShield — API Contracts, Event Schema & Database Design

Base URL: `https://api.<domain>/api/v1`. All bodies JSON (UTF-8). Timestamps RFC 3339 UTC. IDs are UUIDs (generated app-side as UUIDv7). Pydantic v2 models use `model_config = ConfigDict(extra="forbid", strict=True)`.

## 1. Canonical enumerations (single source: `backend/common/enums.py`)

```text
ExecutionKind     : IDEAL_SIMULATOR | NOISY_SIMULATOR | PHYSICAL_HARDWARE
Verdict           : PASS | FAIL | INCONCLUSIVE
ClassicalDecision : ACCEPT | REJECT | ACCEPT_PROVISIONAL
FinalDecision     : ACCEPT | REJECT | PENDING
JobStatus         : QUEUED | RUNNING | SUCCEEDED | FAILED | CANCEL_REQUESTED | CANCELLED | TIMED_OUT | DEAD
Classification    : BENIGN | FORGERY | IMPERSONATION | REPLAY | CHANNEL_MANIPULATION | NOISE_DRIFT |
                    WEB_SQLI | WEB_XSS | AUTH_ABUSE | RATE_ABUSE | INPUT_ABUSE | UNKNOWN
Severity          : INFO | LOW | MEDIUM | HIGH | CRITICAL
ResponseAction    : LOG_ONLY | FLAG | STEP_UP_VERIFICATION | THROTTLE | BLOCK_REQUEST |
                    REVOKE_SESSION | QUARANTINE_IDENTITY | OPEN_INCIDENT
IncidentStatus    : OPEN | INVESTIGATING | CONTAINED | RESOLVED | FALSE_POSITIVE
RunStatus         : QUEUED | PREFLIGHT | RUNNING | COLLECTING | EVALUATING | COMPLETED | FAILED | CANCELLED
EnforcementMode   : BLOCKING | MONITOR
CircuitFamily     : direct | teleport
Basis             : X | Y | Z
Role              : admin | security_analyst | viewer | lab_operator | lab_viewer | auditor
```

**Event types** (`security_events.event_type`): `auth.failed`, `auth.succeeded`, `session.context_change`, `request.verified`, `request.rejected`, `request.stale`, `signature.invalid`, `identity.unknown_key`, `identity.mismatch`, `replay.detected`, `evidence.mac_invalid`, `evidence.params_mismatch`, `evidence.provenance_invalid`, `quantum.verification.passed`, `quantum.verification.failed`, `quantum.verification.inconclusive`, `quantum.channel.anomaly`, `quantum.calibration.drift`, `quantum.job.retried`, `web.sqli.suspected`, `web.xss.suspected`, `auth.enumeration.suspected`, `ratelimit.exceeded`, `input.invalid`, `input.fuzzing.suspected`, `behaviour.anomaly`, `system.degraded`, `lab.safety.violation`.

## 2. Conventions

**Auth:** browsers: HttpOnly session cookie plus a session-bound synchronizer token returned in the JSON body of login and `/auth/me`; frontend keeps the CSRF token in memory and sends `X-CSRF-Token` on mutating methods. No JavaScript-readable CSRF cookie is set. Machines: HMAC headers (Security doc §5.1). **Pagination:** cursor (`?limit=50&cursor=…`), response `{items:[…], next_cursor:string|null}`. **Idempotency:** `Idempotency-Key` header on `POST` that creates jobs/runs/reports. **Versioning:** URL major version.

**Errors** (RFC 9457):
```json
{
  "type": "https://quantumshield.dev/problems/validation-error",
  "title": "Validation failed",
  "status": 422,
  "detail": "shots must be <= 200000",
  "instance": "/api/v1/quantum/jobs",
  "request_id": "0197a1d0-4b0e-7c11-a3a0-5d3c19f0aa01",
  "errors": [{"loc": ["body", "shots"], "code": "less_than_equal", "msg": "shots must be <= 200000"}]
}
```
Status use: 400 malformed, 401 unauthenticated, 403 forbidden/CSRF, 404 not found **or** other org, 409 conflict, 413 too large, 422 validation, 429 rate-limited, 503 degraded (fail-closed).

**Backend object** (returned inside every quantum result):
```json
"backend": {
  "backend_id": "aer-noisy-lab-low",
  "execution_kind": "NOISY_SIMULATOR",
  "provider": "qiskit-aer",
  "provider_job_id": null,
  "noise_model_hash": "sha256:9f2c…",
  "qiskit_version": "1.x",
  "aer_version": "0.x",
  "seed": 424242
}
```

## 3. Endpoints

### 3.1 Authentication
| Method & path | Auth | Purpose |
|---|---|---|
| `POST /auth/login` | none (rate-limited) | start session |
| `POST /auth/mfa/verify` | pre-session | complete TOTP |
| `POST /auth/logout` | session | revoke |
| `GET /auth/me` | session | identity, role, permissions, csrf token |
| `POST /ws/tickets` | session + CSRF | WS ticket |

`POST /auth/login`
```json
// request
{"email": "analyst@example.test", "password": "••••••••••••", "app": "defender"}
// 200
{"user": {"id": "0197a…", "email": "analyst@example.test", "role": "security_analyst", "org_id": "0197a…"},
 "mfa_required": false, "csrf_token": "p9X…", "session_expires_at": "2026-11-07T20:30:00Z"}
// Set-Cookie: __Host-qs_def_sid=…; HttpOnly; Secure; SameSite=Lax; Path=/
```

`POST /ws/tickets`
```json
{"channels": ["events", "incidents", "quantum"]}
// 201
{"ticket": "wst_3kq…", "expires_in": 30, "url": "wss://api.example/ws/v1/stream"}
```

### 3.2 Defender
| Method & path | Perm | Purpose |
|---|---|---|
| `GET/POST /resources`, `GET/PATCH /resources/{id}` | `resources:*` | protected resource management |
| `POST /resources/{id}/credentials` | `resources:write` | issue `key_id`+secret (secret shown once); also `…/rotate`, `…/revoke` |
| `POST /ingest/requests` | machine HMAC | submit request for verification (§4) |
| `GET /ingest/requests/{id}?wait=5` | machine HMAC | long-poll final decision |
| `GET /events` | `events:read` | filter: `type,severity,classification,resource_id,from,to,after_seq` |
| `GET /events/{id}` | `events:read` | detail |
| `GET /incidents`, `GET /incidents/{id}` | `incidents:read` | |
| `PATCH /incidents/{id}` | `incidents:write` | status, assignee |
| `POST /incidents/{id}/notes` | `incidents:write` | |
| `GET /responses`, `POST /responses` | `incidents:read` / `responses:execute` | history / manual action |
| `GET /response-policies`, `PUT /response-policies/{id}` | admin | policy rules |
| `GET /metrics/overview` | `events:read` | dashboard KPIs |
| `GET /quantum/backends` | `quantum:read` | list descriptors + health |
| `POST /quantum/jobs`, `GET /quantum/jobs/{id}`, `POST /quantum/jobs/{id}/cancel` | `quantum:read` / calibrate | §5 |
| `GET /quantum/calibrations`, `POST /quantum/calibrations` | `quantum:calibrate` | |
| `GET /quantum/verifications/{request_id}` | `quantum:read` | statistical report for a request |
| `GET /reports`, `POST /reports`, `GET /reports/{id}` | `reports:*` | evaluation reports |
| `GET /health`, `GET /health/ready` | none / admin detail | liveness / dependency status |

### 3.3 Attack Lab
| Method & path | Perm | Purpose |
|---|---|---|
| `GET/POST /lab/targets`, `GET/PATCH/DELETE /lab/targets/{id}` | `lab:targets:write` | register sandbox targets (SSRF-validated) |
| `POST /lab/targets/{id}/reset` | `lab:runs:execute` | sandbox reset |
| `GET /lab/scenarios`, `GET /lab/scenarios/{id}` | `lab:runs:read` | scenario catalogue |
| `POST /lab/runs` | `lab:runs:execute` | start run (idempotent) |
| `POST /lab/batches` | `lab:runs:execute` | start batch |
| `GET /lab/runs`, `GET /lab/runs/{id}`, `GET /lab/runs/{id}/steps` | `lab:runs:read` | |
| `POST /lab/runs/{id}/cancel`, `POST /lab/batches/{id}/cancel` | `lab:runs:execute` | |
| `POST /lab/experiments`, `GET /lab/experiments/{id}` | `lab:runs:execute` / read | |
| `GET /lab/runs/{id}/evaluation` | `lab:runs:read` | detection effectiveness for run |
| `POST /lab/kill-switch` | admin | global stop |


## 3.8 Frontend-required API addenda (MVP contract)

These endpoints and response shapes are normative for the MVP. They resolve the frontend specification's G-1, G-3, G-4, G-5 and G-7 gaps. All paths below are relative to `/api/v1`; apply the standard authentication, authorization, pagination, error-envelope and organization-isolation rules above.

### `GET /metrics/overview?window=1h|24h|7d`
Permission: `metrics:read`.
```json
{
  "window": "24h",
  "generated_at": "2026-11-10T10:00:00Z",
  "totals": {
    "events": 120,
    "suspicious": 14,
    "classified_attacks": 8,
    "blocked": 6,
    "incidents_open": 3
  },
  "hourly": [
    {"bucket_start": "2026-11-10T09:00:00Z", "events": 12, "suspicious": 2, "blocked": 1}
  ]
}
```
Return a complete series for the requested window (zero-fill empty buckets). Counts are counts, not probabilities.

### `GET /lab/batches/{batch_id}`
Permission: `lab:runs:read`. Return batch metadata, status, aggregate counts, and paginated run references. Enforce organization scoping.

### `GET /lab/experiments`
Permission: `lab:experiments:read`. Cursor-paginated list of experiments owned by the caller's organization. `POST /lab/experiments` creates an experiment and returns its ID.

### `GET /lab/runs`
Permission: `lab:runs:read`. Support cursor pagination and filters `status`, `scenario_id`, `batch_id`, `experiment_id`, and `after` (UTC timestamp). Reject unknown filter values with 422.

### `GET /lab/scenarios/{scenario_id}`
Permission: `lab:scenarios:read`. Include `parameters_schema` as a JSON Schema object, plus scenario version and safety constraints. The server remains authoritative and validates all submitted parameters against the schema and sandbox allowlist.

### Report export
`GET /reports/{report_id}` returns report metadata and structured JSON. `GET /reports/{report_id}/export?format=json|markdown` returns a downloadable file with the correct content type and safe filename. PDF export is future scope, not MVP.

### Recent quantum verifications
`GET /quantum/verifications` supports cursor pagination and filters `resource_id`, `verdict`, `from`, and `to`. `GET /quantum/verifications/{request_id}` returns the verification detail and provenance. These are organization-scoped and permission-protected.


## 4. Ingest and verification

`POST /ingest/requests` (signed; test vector in §8)

```json
// request body
{
  "resource_id": "0197a1c2-0000-7000-8000-000000000001",
  "action": "transfer",
  "payload": {"amount_cents": 1250, "to_account": "SYN-00042"},
  "sandbox_session_id": "sbx-7f31c2",
  "quantum": {"family": "teleport", "link_id": "0197a…", "requested_backend": "aer-noisy-lab-low"}
}
```
```json
// 202 Accepted (classical phase done, quantum pending)
{
  "request_id": "0197a1d1-0c9e-7a22-9a77-9a5a3b2c11f0",
  "classical": "ACCEPT_PROVISIONAL",
  "final": "PENDING",
  "enforcement_mode": "BLOCKING",
  "poll_url": "/api/v1/ingest/requests/0197a1d1-0c9e-7a22-9a77-9a5a3b2c11f0?wait=5",
  "quantum_job_id": "0197a1d1-11b2-70c3-8d0f-9d1a2e44a901"
}
// 200 on classical failure
{"request_id": "0197a1d1-…", "classical": "REJECT", "final": "REJECT",
 "reason": "replay.detected", "event_id": "0197a1d1-2a…"}
```

`GET /ingest/requests/{id}?wait=5` → final:
```json
{
  "request_id": "0197a1d1-0c9e-7a22-9a77-9a5a3b2c11f0",
  "classical": "ACCEPT",
  "quantum": {
    "verdict": "PASS",
    "family": "teleport",
    "settings": 24, "shots_per_setting": 1024,
    "aggregate": {"x2_total": 22.9, "dof": 24, "p_value": 0.53, "alpha": 0.001,
                   "max_abs_z": 2.31, "max_z_threshold": 3.67},
    "structure": {"kappa": [0.97, 0.96, 0.96], "median_direction_error_rad": 0.021, "class": "CONSISTENT"},
    "calibration_id": "0197a…",
    "backend": {"backend_id": "aer-noisy-lab-low", "execution_kind": "NOISY_SIMULATOR", "provider": "qiskit-aer",
                 "provider_job_id": null, "noise_model_hash": "sha256:9f2c…", "seed": 424242}
  },
  "final": "ACCEPT",
  "classification": "BENIGN",
  "decided_at": "2026-11-07T10:15:03.412Z"
}
```
(The numbers above are *illustrative* examples of shape only.)

## 5. Quantum jobs

```json
// POST /quantum/jobs  (Idempotency-Key header)
{
  "job_type": "tomography_teleport",           // verification | calibration | tomography_teleport | bell_witness | experiment
  "backend_id": "aer-noisy-lab-low",
  "shots": 4096,
  "seed": 424242,
  "timeout_s": 120,
  "spec": {
    "states": [{"theta": 1.0471975512, "phi": 0.0}, {"theta": 1.5707963268, "phi": 1.5707963268}],
    "bases": ["X", "Y", "Z"]
  }
}
// 201
{"id": "0197a1d3-…", "status": "QUEUED", "created_at": "2026-11-07T10:20:00Z",
 "backend": {"backend_id": "aer-noisy-lab-low", "execution_kind": "NOISY_SIMULATOR", "provider": "qiskit-aer",
              "provider_job_id": null, "noise_model_hash": "sha256:9f2c…", "seed": 424242}}
```
```json
// GET /quantum/jobs/{id} once SUCCEEDED (tomography)
{
  "id": "0197a1d3-…", "status": "SUCCEEDED", "attempts": 1, "duration_ms": 8412,
  "backend": { "…": "…" },
  "results": [
    {"state": {"theta": 1.0471975512, "phi": 0.0},
     "bloch_estimate": [0.861, 0.004, 0.489],
     "fidelity": 0.973, "fidelity_se": 0.0047,
     "outcome_uniformity_p": 0.41}
  ],
  "classical_bound_average_fidelity": 0.6667
}
```

## 6. WebSocket

`GET wss://api.<domain>/ws/v1/stream?ticket=wst_…`

Client → server:
```json
{"op": "subscribe", "channels": ["events", "incidents"], "last_seq": {"events": 10234}}
{"op": "pong"}
```
Server → client envelope:
```json
{
  "channel": "events",
  "seq": 10235,
  "ts": "2026-11-07T10:15:03.500Z",
  "type": "security_event.created",
  "data": {
    "id": "0197a1d1-2a11-7000-9d12-aa0300000001",
    "event_type": "replay.detected",
    "severity": "MEDIUM",
    "classification": "REPLAY",
    "resource_id": "0197a1c2-0000-7000-8000-000000000001",
    "summary": "Duplicate nonce for key 0197a…",
    "response": {"action": "BLOCK_REQUEST"}
  }
}
```
Types: `security_event.created`, `incident.created|updated`, `response.executed`, `quantum.job.updated`, `quantum.verdict`, `lab.run.progress|completed`, `system.health`. Close codes: 4401 auth expired, 4403 forbidden channel, 1013 backpressure.

## 7. Lab runs

```json
// POST /lab/runs
{
  "scenario_id": "S4-channel-intercept-resend",
  "target_id": "0197a1e0-…",
  "parameters": {"model": "intercept_resend_Z", "fraction": 0.5, "trials": 200, "noise_profile": "lab-low"},
  "seed": 20261107,
  "limits": {"max_requests": 400, "max_rps": 10, "max_duration_s": 300}
}
// 201
{"id": "0197a1e1-…", "status": "QUEUED", "config_hash": "sha256:b1d4…", "seed": 20261107,
 "safety": {"target_registered": true, "target_expires_at": "2026-12-01T00:00:00Z"}}
```
```json
// GET /lab/runs/{id}/evaluation  (available after EVALUATING)
{
  "run_id": "0197a1e1-…",
  "scenario_id": "S4-channel-intercept-resend",
  "trials_attack": 200, "trials_benign": 1000,
  "tp": 198, "fn": 2, "fp": 3, "tn": 997,
  "tpr": 0.99, "tpr_ci95": [0.967, 0.995],
  "fpr": 0.003, "fpr_ci95": [0.001, 0.009],
  "median_detection_latency_ms": 1240,
  "backend": {"execution_kind": "NOISY_SIMULATOR", "backend_id": "aer-noisy-lab-low", "noise_model_hash": "sha256:9f2c…"},
  "noise_budget_statement": "Isotropic contraction down to κ=0.90 is accepted by design."
}
```
(Illustrative values.)

## 8. Signing test vector (SEC-1)

Secret (UTF-8): `qs-test-vector-secret-0123456789abcdef`

Raw body: `{"resource_id":"0197a1c2-0000-7000-8000-000000000001","action":"transfer","amount_cents":1250}`

| Item | Value |
|---|---|
| `X-QS-Key-Id` | `0197a1c2-0000-7000-8000-0000000000aa` |
| `X-QS-Timestamp` | `1767225600000` |
| `X-QS-Nonce` | `c3ludGhldGljLW5vbmNlLTAwMQ` |
| `X-QS-Body-SHA256` | `70a0b79b71e14ec0c16e4cece71ad1e4bef4fddedf94e68d8ef875826375584d` |
| Canonical string | `QS1\nPOST\n/api/v1/ingest/requests\n\n0197a1c2-0000-7000-8000-0000000000aa\n1767225600000\nc3ludGhldGljLW5vbmNlLTAwMQ\n70a0b79b71e14ec0c16e4cece71ad1e4bef4fddedf94e68d8ef875826375584d` (empty query line) |
| `X-QS-Signature` (HMAC-SHA256, base64url, no padding) | `XCi3vvJ7Fq-Uiw6RBqKdaEizDyUII5347IvU57DFCDQ` |

(The vector was computed with Python's `hmac`/`hashlib`; implementers must still reproduce it in their own tests and use a fixed "now" when testing the timestamp window.)

## 9. Database schema (PostgreSQL 16)

Conventions: every tenant table has `org_id uuid NOT NULL`; RLS enabled; `created_at timestamptz DEFAULT now()`. Enums are `CREATE TYPE` mirrors of §1.

### 9.1 Roles and RLS
```sql
CREATE ROLE qs_migrator; CREATE ROLE qs_api LOGIN; CREATE ROLE qs_worker LOGIN;
CREATE ROLE qs_detect LOGIN; CREATE ROLE qs_eval LOGIN;

-- RLS pattern, applied to every tenant table:
ALTER TABLE security_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON security_events
  USING (org_id = current_setting('app.org_id', true)::uuid);

-- Ground truth: only evaluation role may read
REVOKE ALL ON ground_truth_labels FROM qs_api, qs_worker, qs_detect;
GRANT SELECT ON ground_truth_labels TO qs_eval;
GRANT INSERT ON ground_truth_labels TO qs_api;   -- write-only for the API
```

### 9.2 Core tables
```sql
CREATE TABLE organizations (
  id uuid PRIMARY KEY, name text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());

CREATE TABLE users (
  id uuid PRIMARY KEY, org_id uuid NOT NULL REFERENCES organizations(id),
  email citext NOT NULL, password_hash text NOT NULL, role role_enum NOT NULL,
  totp_secret_enc bytea, is_active boolean NOT NULL DEFAULT true,
  failed_logins int NOT NULL DEFAULT 0, locked_until timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(), UNIQUE (org_id, email));

CREATE TABLE sessions (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, user_id uuid NOT NULL REFERENCES users(id),
  app text NOT NULL CHECK (app IN ('defender','lab')),
  token_hash bytea NOT NULL UNIQUE, csrf_secret bytea NOT NULL,
  ip inet, user_agent text, created_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL, expires_at timestamptz NOT NULL, revoked_at timestamptz);

CREATE TABLE protected_resources (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, name text NOT NULL, base_url text,
  enforcement_mode enforcement_mode NOT NULL DEFAULT 'BLOCKING',
  is_sandbox boolean NOT NULL DEFAULT false, status text NOT NULL DEFAULT 'ACTIVE',
  allowed_backends text[] NOT NULL DEFAULT '{aer-ideal-1}',
  created_at timestamptz NOT NULL DEFAULT now(), UNIQUE (org_id, name));

CREATE TABLE api_credentials (
  key_id uuid PRIMARY KEY, org_id uuid NOT NULL, resource_id uuid NOT NULL REFERENCES protected_resources(id),
  kind text NOT NULL CHECK (kind IN ('hmac_req','quantum_k')),
  secret_enc bytea NOT NULL, dek_enc bytea NOT NULL, kek_id text NOT NULL,
  status text NOT NULL DEFAULT 'ACTIVE', expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(), revoked_at timestamptz);

CREATE TABLE sandbox_targets (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, name text NOT NULL, host text NOT NULL, port int NOT NULL CHECK (port BETWEEN 1 AND 65535),
  ip_pins inet[] NOT NULL, network_zone text NOT NULL CHECK (network_zone = 'qs-lab'),
  status text NOT NULL DEFAULT 'ACTIVE', signature bytea NOT NULL,
  expires_at timestamptz NOT NULL, created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now());
```

### 9.3 Quantum tables
```sql
CREATE TABLE quantum_backends (
  backend_id text PRIMARY KEY, execution_kind execution_kind NOT NULL, provider text NOT NULL,
  noise_model_hash text, noise_profile jsonb, supports_dynamic_circuits boolean NOT NULL,
  n_qubits int NOT NULL, enabled boolean NOT NULL DEFAULT true,
  CONSTRAINT provenance_aer CHECK (provider <> 'qiskit-aer' OR execution_kind IN ('IDEAL_SIMULATOR','NOISY_SIMULATOR')),
  CONSTRAINT provenance_noisy CHECK (execution_kind <> 'NOISY_SIMULATOR' OR noise_model_hash IS NOT NULL));

CREATE TABLE calibrations (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, backend_id text NOT NULL REFERENCES quantum_backends,
  family circuit_family NOT NULL, noise_model_hash text, windows int NOT NULL, shots_per_setting int NOT NULL,
  settings jsonb NOT NULL,         -- [{theta,phi,basis,p_bar,dispersion_phi}, ...]
  status text NOT NULL CHECK (status IN ('VALID','STALE','REJECTED')),
  valid_until timestamptz, created_at timestamptz NOT NULL DEFAULT now(), job_id uuid);

CREATE TABLE quantum_jobs (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, job_type text NOT NULL, status job_status NOT NULL DEFAULT 'QUEUED',
  backend_id text NOT NULL REFERENCES quantum_backends, execution_kind execution_kind NOT NULL,
  provider_job_id text, noise_model_hash text,
  shots int NOT NULL CHECK (shots BETWEEN 1 AND 200000), seed bigint, spec jsonb NOT NULL,
  idempotency_key text NOT NULL, attempts int NOT NULL DEFAULT 0, timeout_s int NOT NULL DEFAULT 30,
  lease_until timestamptz, heartbeat_at timestamptz, error text,
  requested_by uuid, request_id uuid, created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz, finished_at timestamptz,
  UNIQUE (org_id, idempotency_key),
  CONSTRAINT hw_needs_provider CHECK (execution_kind <> 'PHYSICAL_HARDWARE' OR provider_job_id IS NOT NULL));

CREATE TABLE quantum_results (
  job_id uuid NOT NULL REFERENCES quantum_jobs(id), circuit_index int NOT NULL,
  setting jsonb NOT NULL, counts jsonb NOT NULL, shots int NOT NULL, execution_kind execution_kind NOT NULL,
  PRIMARY KEY (job_id, circuit_index));

CREATE TABLE quantum_evidence (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, request_id uuid NOT NULL, job_id uuid REFERENCES quantum_jobs(id),
  family circuit_family NOT NULL, params_digest bytea NOT NULL, evidence_digest bytea NOT NULL,
  mac bytea NOT NULL, verdict verdict, statistics jsonb, structure_class text,
  calibration_id uuid REFERENCES calibrations(id), execution_kind execution_kind NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, evidence_digest));
```

### 9.4 Request, event, detection, response, incident
```sql
CREATE TABLE ingest_requests (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, resource_id uuid NOT NULL, key_id uuid,
  sandbox_session_id text, method text, path text, body_sha256 bytea, ts_client timestamptz, nonce text,
  classical classical_decision NOT NULL, final final_decision NOT NULL DEFAULT 'PENDING',
  source_ip inet, user_agent text, received_at timestamptz NOT NULL DEFAULT now(), decided_at timestamptz);

CREATE TABLE request_nonces (
  key_id uuid NOT NULL, nonce text NOT NULL, ts_client timestamptz NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (key_id, nonce))
  PARTITION BY RANGE (received_at);     -- daily partitions, 7-day retention

CREATE TABLE security_events (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, seq bigint GENERATED ALWAYS AS IDENTITY,
  event_type text NOT NULL, severity severity NOT NULL, resource_id uuid, request_id uuid, key_id uuid,
  sandbox_session_id text, source_ip inet, payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX ON security_events (org_id, created_at DESC);
CREATE INDEX ON security_events (org_id, event_type, created_at DESC);
CREATE INDEX ON security_events (org_id, seq);

CREATE TABLE detections (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, event_id uuid NOT NULL REFERENCES security_events(id),
  classification classification NOT NULL, confidence real NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  rule_ids text[] NOT NULL, features jsonb, detector_version text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());

CREATE TABLE response_actions (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, detection_id uuid REFERENCES detections(id),
  incident_id uuid, action response_action NOT NULL, target_type text, target_id text,
  mode text NOT NULL CHECK (mode IN ('AUTO','MANUAL')), status text NOT NULL, reason text,
  executed_by uuid, created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz, reverted_at timestamptz);

CREATE TABLE incidents (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, title text NOT NULL, status incident_status NOT NULL DEFAULT 'OPEN',
  severity severity NOT NULL, classification classification NOT NULL, resource_id uuid,
  dedup_key text NOT NULL, first_seen timestamptz NOT NULL, last_seen timestamptz NOT NULL,
  event_count int NOT NULL DEFAULT 1, assignee uuid, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, dedup_key, status) DEFERRABLE);
CREATE TABLE incident_events (incident_id uuid REFERENCES incidents(id), event_id uuid REFERENCES security_events(id), PRIMARY KEY (incident_id, event_id));
CREATE TABLE incident_notes (id uuid PRIMARY KEY, incident_id uuid NOT NULL REFERENCES incidents(id), author uuid NOT NULL, body text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
```
Incident correlation: `dedup_key = classification || ':' || resource_id || ':' || coalesce(key_id, source_ip)`; an event within 15 minutes of an incident's `last_seen` with the same key attaches to it, else opens a new incident.

### 9.5 Lab and evaluation tables
```sql
CREATE SCHEMA lab;
CREATE TABLE lab.attack_scenarios (id text PRIMARY KEY, version int NOT NULL, category classification NOT NULL, definition jsonb NOT NULL, definition_sha256 bytea NOT NULL);

CREATE TABLE lab.attack_runs (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, batch_id uuid, experiment_id uuid,
  scenario_id text NOT NULL, scenario_version int NOT NULL, target_id uuid NOT NULL REFERENCES sandbox_targets(id),
  status run_status NOT NULL DEFAULT 'QUEUED', parameters jsonb NOT NULL, config_hash bytea NOT NULL, seed bigint NOT NULL,
  git_sha text, qiskit_version text, aer_version text, noise_model_hash text, execution_kind execution_kind,
  sandbox_session_id text NOT NULL, started_by uuid NOT NULL, started_at timestamptz, finished_at timestamptz,
  safety_log jsonb NOT NULL DEFAULT '[]', created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, config_hash, seed, batch_id));

CREATE TABLE lab.attack_run_steps (
  run_id uuid NOT NULL REFERENCES lab.attack_runs(id), step_index int NOT NULL, kind text NOT NULL,
  request_summary jsonb, response_status int, started_at timestamptz, duration_ms int, completed boolean NOT NULL DEFAULT false,
  PRIMARY KEY (run_id, step_index));

-- Restricted: written by API at run creation, read only by evaluation
CREATE TABLE ground_truth_labels (
  run_id uuid NOT NULL, trial_index int NOT NULL, sandbox_session_id text NOT NULL,
  is_attack boolean NOT NULL, true_class classification NOT NULL, variant text, ts_start timestamptz, ts_end timestamptz,
  PRIMARY KEY (run_id, trial_index));

CREATE TABLE evaluation_reports (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, kind text NOT NULL, run_ids uuid[] NOT NULL,
  metrics jsonb NOT NULL, config jsonb NOT NULL, config_hash bytea NOT NULL, environment jsonb NOT NULL,
  execution_kinds execution_kind[] NOT NULL, created_by uuid, created_at timestamptz NOT NULL DEFAULT now(),
  artifact_uri text);
```

### 9.6 Audit
```sql
CREATE TABLE audit_log (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, org_id uuid NOT NULL, ts timestamptz NOT NULL DEFAULT now(),
  actor_type text NOT NULL, actor_id text, action text NOT NULL, object_type text, object_id text,
  ip inet, outcome text NOT NULL, details jsonb, prev_hash bytea, hash bytea NOT NULL);
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM PUBLIC, qs_api, qs_worker, qs_detect, qs_eval;
-- insertion via SECURITY DEFINER function append_audit(...) computing hash = sha256(prev_hash || row_json)
```

### 9.7 Retention and indexes
`security_events` 90 days hot (partition monthly), 1 year archived; `request_nonces` 7 days; `quantum_results` 180 days; `audit_log` 1 year minimum; `sessions` purged 30 days after expiry. Add indexes on all FK columns, `quantum_jobs (status, lease_until)` for the janitor, `ingest_requests (org_id, received_at DESC)`.

## 10. Acceptance criteria

| ID | Criterion |
|---|---|
| API-1 | The OpenAPI document generated by FastAPI contains every endpoint in §3 and validates in CI (`openapi-spec-validator`); TS client generation succeeds. |
| API-2 | Every response schema that includes quantum results includes a required `backend.execution_kind`; contract test enforces it. |
| API-3 | All enums in §1 are defined once and imported by Pydantic models, SQLAlchemy models, and the OpenAPI schema; a test compares DB enum labels with Python enums. |
| API-4 | Alembic migration from empty DB creates all tables, constraints, RLS policies, and roles; downgrade/upgrade round-trips on CI. |
| API-5 | DB `CHECK` tests: inserting an Aer backend with `PHYSICAL_HARDWARE`, a noisy simulator without hash, or hardware without provider job id fails. |
| API-6 | Signing vector in §8 verifies in server tests; mutating any one input fails. |
| API-7 | All 4xx/5xx responses follow `application/problem+json` and contain `request_id`. |
| API-8 | WebSocket integration test: ticket single-use, wrong Origin rejected, `seq` monotonic, resume from `last_seq` works. |
