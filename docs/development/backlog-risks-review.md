# QuantumShield — Implementation Backlog, Review Criteria & Risk Register

Audience: Antigravity (implementation). Sizes: S ≤ ½ day, M ≈ 1 day, L ≈ 2–3 days. Every story is "done" only when its referenced acceptance IDs pass in CI.

## 1. Kick-off checklist (first hour of Day 2)

1. Create GitHub repo `quantumshield`; commit `docs/` exactly as delivered (paths preserved).
2. Add `.gitignore`, `README.md` (link to `docs/README.md`), `.env.example` (names only), `CODEOWNERS`.
3. Set up `pyproject.toml` (single lockfile) and `pnpm-workspace.yaml`; pin Python 3.11+ and record the Qiskit/Aer versions chosen (record versions; verify API names such as `if_test` against the installed version).
4. Start `docker-compose.yml` with `postgres`, `redis` only; add services as they appear.
5. Enable CI skeleton (lint, type-check, tests) and secret scanning *before* any feature code.
6. Open an "Open decisions" issue (§6).

## 2. Epics and stories

Priority: P0 (critical path), P1 (needed for MVP), P2 (stretch).

### E0 — Foundation
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E0-1 | Monorepo scaffold per Architecture §13 | M | P0 | — | ARC-1 |
| E0-2 | `backend/common`: settings (pydantic-settings), logging w/ redaction, error types (problem+json), enums from API doc §1 | M | P0 | E0-1 | API-3, API-7, SEC-10 |
| E0-3 | CI: ruff, mypy, pytest, eslint, tsc, Semgrep rules, gitleaks, OpenAPI export + TS client | M | P0 | E0-1 | SEC-7 |
| E0-4 | docker-compose dev stack with health checks | S | P0 | E0-1 | — |

### E1 — Database and migrations
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E1-1 | SQLAlchemy models + Alembic baseline from API doc §9 | L | P0 | E0-2 | API-4, API-5 |
| E1-2 | Roles, grants, RLS policies, `SET LOCAL app.org_id` middleware | M | P0 | E1-1 | SEC-4, ARC-3 |
| E1-3 | Audit log append function + hash-chain verifier | M | P1 | E1-1 | SEC-9 |
| E1-4 | Nonce table partitioning + retention job | S | P1 | E1-1 | SEC-3 |

### E2 — Auth, sessions, RBAC, signing
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E2-1 | Argon2id login, throttling, TOTP | M | P0 | E1-1 | SEC-11 |
| E2-2 | Server-side sessions, cookies, CSRF, Origin check | M | P0 | E2-1 | SEC-5 |
| E2-3 | RBAC dependency + permission matrix | M | P0 | E2-2 | SEC-4 |
| E2-4 | HMAC request-signature verifier + client helper (Python + TS) | M | P0 | E1-1 | API-6, SEC-1 |
| E2-5 | Redis nonce claim + DB fallback + Redis-epoch rule | M | P0 | E2-4 | SEC-2, SEC-3 |
| E2-6 | Envelope encryption for secrets, key issue/rotate/revoke | M | P1 | E1-1 | SEC-10 |
| E2-7 | Rate limiter (Redis Lua token bucket) | M | P1 | E0-4 | SEC-11 |

### E3 — Quantum engine (library, no web)
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E3-1 | Backend abstraction + `AerIdeal`, `AerNoisy`; provenance validators | M | P0 | E0-2 | Q-13 |
| E3-2 | State prep + basis rotation builders, analytic expectation functions | M | P0 | E3-1 | Q-1, Q-2, Q-3 |
| E3-3 | Bell pair builder + witness estimator + CHSH (optional) | M | P1 | E3-2 | Q-4, Q-5 |
| E3-4 | Teleportation circuit with classical feed-forward, tomography estimator | L | P0 | E3-2 | Q-6, Q-7, Q-8 |
| E3-5 | Noise model factory + profiles + hash | M | P0 | E3-1 | Q-9 |
| E3-6 | Counts parser (endianness-safe, register-aware) | S | P0 | E3-1 | Q-14 |
| E3-7 | Calibration pipeline + over-dispersion + records | L | P0 | E3-5 | Q-10 |
| E3-8 | Verification statistics: per-setting, aggregate, localised, structure analysis, power calculator | L | P0 | E3-7 | Q-11, Q-12 |
| E3-9 | QVE derivation (HKDF), evidence object, MAC, digest | M | P0 | E3-2, E2-6 | API-6 (QVE vectors), T7/T8 tests |
| E3-10 | Channel-manipulation models (§9.6) | M | P1 | E3-4 | Q-12 |

### E4 — Worker and jobs
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E4-1 | Celery app, task wrappers, chunked execution, cancel flag | L | P0 | E3-1, E1-1 | ARC-4 |
| E4-2 | Lease/heartbeat janitor, retry policy, DLQ | M | P1 | E4-1 | ARC-4 |
| E4-3 | Job API endpoints (create/get/cancel), idempotency, quotas | M | P0 | E4-1, E2-3 | API-1 |

### E5 — Ingest, detection, response, incidents
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E5-1 | `/ingest/requests` two-phase decision + long-poll | L | P0 | E2-5, E4-3, E3-9 | SEC-2, API-2 |
| E5-2 | Event store + normalisation (D0) | M | P0 | E1-1 | EVAL-1 |
| E5-3 | Rule engine R-* (D2) incl. SQLi/XSS tokenizers | L | P0 | E5-2 | EVAL-1 |
| E5-4 | Behavioural baselines (D4) | M | P1 | E5-2 | EVAL-1 |
| E5-5 | Fusion + severity (D5–D6) | M | P0 | E5-3 | EVAL-2 |
| E5-6 | Incident correlation + lifecycle API | M | P1 | E5-5 | API-1 |
| E5-7 | Response engine + policy + safeguards | L | P0 | E5-5 | EVAL-3 |

### E6 — Realtime
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E6-1 | WS tickets, handshake, Redis pub/sub fan-out, seq, resume | L | P0 | E2-2 | API-8, ARC-6 |

### E7 — Attack Lab backend
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E7-1 | Target registry, validators (SSRF/IP pin), signing, expiry | M | P0 | E1-1 | LAB-1 |
| E7-2 | Safety guard library + egress firewall config + kill switch | M | P0 | E7-1 | LAB-1, LAB-2, ARC-7 |
| E7-3 | Sandbox target app (vulnerable/hardened modes, synthetic data, reset) | L | P0 | E0-4 | LAB-5 |
| E7-4 | Runner framework, run lifecycle, cancel, seeds, config hash | L | P0 | E7-2 | LAB-3, LAB-4 |
| E7-5 | Scenarios 1–3 (forgery, impersonation, replay) | L | P0 | E7-4, E5-1 | LAB-5 |
| E7-6 | Scenario 4 (channel manipulation) with channel profiles | L | P0 | E7-4, E3-10 | LAB-5, LAB-7 |
| E7-7 | Scenario 5.1–5.5 + payload corpora (fixed files, hashed) | L | P1 | E7-4, E7-3 | LAB-5 |
| E7-8 | Ground-truth writer and restricted table | S | P0 | E1-2 | LAB-6 |

### E8 — Evaluation
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E8-1 | Trial matching + metrics + Wilson/CP/bootstrap | L | P0 | E7-8, E5-5 | EVAL-4 |
| E8-2 | Experiment/batch orchestration, arms A0/A1/A2 | L | P1 | E7-4, E8-1 | EVAL-5 |
| E8-3 | Report generator (JSON+MD), validation rules | M | P1 | E8-1 | EVAL-6 |

### E9 — Frontends
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E9-1 | Next.js apps, Tailwind, generated API client, auth flows, CSP via middleware | L | P0 | E2-3, E0-3 | SEC-8 |
| E9-2 | Defender: overview, live event stream, resources, incidents, responses | L | P0 | E9-1, E6-1 | EVAL-8 |
| E9-3 | Defender: quantum status (backend badge, calibration, verdict stats, jobs) | M | P1 | E9-1, E4-3 | API-2 |
| E9-4 | Defender: reports and system health | M | P1 | E9-1, E8-3 | — |
| E9-5 | Lab: targets, scenario catalogue, run/batch config, live progress, cancel | L | P0 | E9-1, E7-4 | LAB-3 |
| E9-6 | Lab: evaluation views and experiment comparison | M | P1 | E9-5, E8-3 | EVAL-6 |
| E9-7 | UI renders untrusted strings as text only; Playwright XSS test | S | P0 | E9-2 | Scenario 5.2 |

### E10 — Hardening and deployment
| ID | Story | Size | Pri | Depends | Acceptance |
|---|---|---|---|---|---|
| E10-1 | Dockerfiles (non-root, minimal), compose for all services | M | P1 | all | ARC-4, ARC-5 |
| E10-2 | Vercel projects for both apps; env config; domain plan | S | P1 | E9-1 | — |
| E10-3 | Staging deploy of API/worker/Redis/Postgres; fail-closed drills | M | P2 | E10-1 | ARC-5 |
| E10-4 | Full e2e: Scenarios 1–5 → events → responses → report | L | P1 | E7-*, E8-* | LAB-5, EVAL-5 |

### Suggested sequencing
- **Day 2:** E0, E1-1, E1-2, E2-1…E2-4, E3-1, E3-2 (critical path: signing + quantum core in parallel).
- **Day 3:** E2-5, E3-4…E3-8, E4-1, E5-1 skeleton, E5-2.
- **Day 4:** E3-9, E3-10, E5-3…E5-5, E6-1, E7-1…E7-2.
- **Day 5:** E5-7, E7-3…E7-6, E8-1, E9-1.
- **Day 6+:** E9-2…E9-6, E7-7, E8-2/3, E10, hardening, full e2e, documentation sync.

## 3. Definition of Done (every story)
1. Code + tests merged via PR with ≥ 1 review against §4.
2. Referenced acceptance IDs pass in CI (not just locally).
3. Types complete (mypy `--strict` for `backend/`, `tsc --noEmit`).
4. OpenAPI/TS client regenerated if the API changed.
5. Docs updated where behaviour deviates from these specs, with an ADR (`docs/development/adr-NNN.md`) for any deviation.
6. No new secrets, no `TODO(security)`.

## 4. Code-review criteria

**Security**
- [ ] No string-built SQL; no `eval/exec/pickle/shell=True`; no secrets in code, logs, exceptions.
- [ ] Every route has an explicit permission dependency; object lookups are org-scoped; negative tests exist.
- [ ] Constant-time comparison for MAC/signature/token checks.
- [ ] Mutating routes enforce CSRF + Origin (cookie auth) or signature (machine auth).
- [ ] New attacker-controlled strings are length-capped and rendered as text in the UI.
- [ ] Failure paths are **fail-closed** (Redis/DB/worker outages on BLOCKING resources).

**Quantum correctness**
- [ ] Gate conventions match Quantum spec §0–§5 (RZ sign, `sdg` before `h` for Y, little-endian parsing).
- [ ] Teleportation has real classical feed-forward (`if_test`); corrections on the right qubit and bit pairing (`c1→X`, `c0→Z`).
- [ ] Every result carries `backend.execution_kind`; Aer never labelled hardware; calibration keyed by `(backend, family, noise hash)`.
- [ ] Statistical tests check expected-count validity and record which test was used; variance inflation $c$ applied; multiple-testing handled.
- [ ] Seeds recorded; tests are deterministic with fixed seeds and use tolerance ≥ 4 SE (never exact equality on sampled probabilities).
- [ ] No claims in UI/docs/strings that quantum circuits secure HTTP/DB/TLS.

**Architecture**
- [ ] Detection code does not import or query ground-truth modules.
- [ ] Long work is in the worker, not in a request handler; jobs idempotent; cancellation points exist.
- [ ] Lab code paths pass through the safety guard; no direct `httpx` calls from scenarios.
- [ ] Postgres is source of truth; Redis loss does not lose audit data.

**Quality**
- [ ] Unit + integration tests; mocks only at I/O boundaries; no sleeps for synchronisation (use events/polling with timeouts).
- [ ] Clear error messages without internals; structured logs with `request_id`.
- [ ] Reasonable performance: ingest classical phase p95 < 100 ms (local), WS fan-out < 250 ms.

## 5. Risk register

| ID | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Overclaiming quantum security (scientific/reputational) | H | H | Mandatory statements (Security §1, Quantum §11); review checklist; report validators | Architecture |
| R2 | Qiskit/Aer API drift (e.g., dynamic circuits, noise API) | M | M | Pin versions; compatibility test suite; isolate in `quantum_engine`; spec fragments are *sketches* to be verified against pinned version | Implementation |
| R3 | Simulation cost for many circuits/shots slows verification | M | M | m=24 × N=1024 default; analytic expectations for ideal; chunking; worker scaling; optional caching of calibrations | Implementation |
| R4 | Statistical test misuse (small expected counts, dependence) | M | H | Validity checks (Quantum §8.3); tests with known-null simulations; independence via fresh seeds | Architecture/Impl |
| R5 | Noise-mimicking attacker undetectable | H | M | Document noise budget; report honestly; keep $\kappa_{\min}$ tight; don't hide in evaluation | Architecture |
| R6 | Attack Lab misuse / sandbox escape | L | H | Network-enforced egress, signed registry, double validation, kill switch, audit | Implementation |
| R7 | Ground-truth leakage inflates metrics | M | H | Separate role/table, tests ARC-3/EVAL-7 | Implementation |
| R8 | Redis outage weakens replay protection | M | H | Fail closed; DB nonce fallback; Redis-epoch rule | Implementation |
| R9 | WebSocket scaling/state on container host | M | M | Redis pub/sub fan-out; stateless API; sticky not required; resume via REST | Implementation |
| R10 | Vercel misuse (backend/WS hosting expectations) | M | M | Frontends only; API on container host; same-site domains | DevOps |
| R11 | Cookie/CSRF misconfiguration across subdomains | M | H | `__Host-` cookies, Origin allowlist, distinct app cookies, tests SEC-5 | Implementation |
| R12 | Scope creep (building "everything" shallowly) | H | M | P0/P1/P2 priorities; vertical slice first (signed ingest → QVE → verdict → event → UI) | Lead |
| R13 | Calibration poisoning / stale baselines | M | M | Role limits, 2-window rule, drift alarms, `INCONCLUSIVE` fail-closed | Architecture |
| R14 | Supply-chain compromise | L | H | Lockfiles with hashes, Dependabot, minimal images, SBOM | DevOps |
| R15 | Hardware integration expectations | M | L | Abstraction ready; explicit "not in v1"; dynamic-circuit support check | Architecture |
| R16 | Test flakiness from sampling | H | L | Seeded runs; 4-SE tolerances; separate slow statistical suite | Implementation |

## 6. Open decisions (for the project owner / Antigravity)

1. Hosting provider for API/worker/Postgres/Redis (Fly.io, Render, Cloud Run, ECS…) and domain names.
2. Celery vs. an async queue: this spec chooses Celery (prefork); revisit only with a measured reason.
3. MFA scope for v1 (TOTP required for `admin` only vs. all).
4. Whether to include optional CHSH checks in MVP (spec marks them P1).
5. The truncated remainder of the master assignment (after Scenario 5): confirm no additional required deliverables.
6. Retention periods in API doc §9.7 are defaults; confirm.

## 7. Vertical slice (first demonstrable milestone)

`alice` (sandbox app) → signed `/ingest/requests` → classical checks → quantum job on `aer-noisy-lab-low` → verdict → event + WebSocket → Defender live stream shows PASS; then Scenario 3 (replay) blocked and displayed; then Scenario 4 (`intercept_resend_Z`) FAIL with structure analysis; then a report with CIs. This slice touches every architectural layer and validates the specs early.
