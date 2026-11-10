# QuantumShield — Attack Lab Methodology

## 1. Purpose and non-negotiable safety rules

The Attack Lab tests the Defender **only** against registered, isolated, authorized sandbox targets using synthetic data. It is never pointed at third-party or production systems.

| # | Rule | Enforcement |
|---|---|---|
| S1 | A run MUST reference a `sandbox_target` in state `ACTIVE`, registered by a `lab_operator`/`admin` | API check at run creation + runner check before each step |
| S2 | Target registry entries are **signed** (HMAC by API) and contain `host`, `port`, `ip_pins[]`, `network_zone=qs-lab`, `owner_org`, `expires_at` | Runner verifies signature; tampering ⇒ abort + `lab.safety.violation` |
| S3 | Targets MUST resolve to private sandbox addresses (RFC 1918 / the `qs-lab` docker network). Public IPs, loopback of the API host, cloud metadata addresses are rejected | Registration validator + DNS re-resolve and IP pin at run time |
| S4 | Egress firewall: the runner container can reach only the API and registered sandbox IPs | Docker `internal` network / cloud security group — **network enforced**, not only code |
| S5 | Synthetic data only: identities, payloads, "customers" are generated from a seeded generator; no real credentials or PII | CI test on fixtures; generator is the only data source |
| S6 | Every scenario declares a hard `max_requests`, `max_rps`, `max_duration_s`; defaults: 2 000 requests, 20 rps, 300 s | Runner rate limiter; scenario schema validation |
| S7 | Cancellation: per-run cancel and a global **kill switch** (`lab_enabled=false` setting) stop all runs within 5 s | Cooperative check each step + container stop fallback |
| S8 | Attacks that damage state (SQLi, XSS payload storage) act only on the sandbox DB, which is reset (`sandbox_reset`) after every run | Reset job; sandbox DB credentials separate from platform DB |
| S9 | Conventional attack payloads are taken from a **curated, fixed corpus** in the repo (no live exploit frameworks, no network scanning, no zero-day tooling) | Code review gate; corpus file hash in run record |
| S10 | Every run records `config_hash`, `seed`, `git_sha`, operator, target, safety checks passed | `attack_runs` row |
| S11 | Quantum "attacks" operate only on the simulated channel via a **channel profile** attached to a sandbox link; the real API surface is not given attacker privileges | API: channel profile settable only for links tagged `sandbox` |

Violations raise `lab.safety.violation`, abort the run, and create a `CRITICAL` incident in the platform (not in sandbox data).

## 2. Lab architecture recap

- **Attack runner** (Z5) executes scenario definitions. **Sandbox target** is a small app with a synthetic customer DB, login form, search endpoint, comment endpoint, and a protected `/transfer` action that calls the Defender's ingest API with signed requests (so the Defender sees it as a protected app).
- **Identities:** `alice`, `bob`, `mallory` — synthetic principals, each with their own `key_id`, $K_{req}$, $K_q$ (generated per run unless the scenario states otherwise).
- **Ground truth:** written at run creation to `ground_truth_labels` (restricted). The Defender never sees it.

### Scenario definition schema (YAML in `backend/attack_engine/scenarios/`)

```yaml
id: S3-replay-exact
version: 1
category: REPLAY
description: Re-send a captured valid signed request.
limits: { max_requests: 200, max_rps: 10, max_duration_s: 120 }
preconditions: [target_active, identity_registered:alice, defender_calibration_valid]
parameters:
  variant: exact            # exact | delayed | modified_nonce | cross_session
  delays_s: [1, 5, 30, 90]
  repetitions: 25
expected:
  classification: REPLAY
  response: BLOCK_REQUEST
  events: [replay.detected]
pass: { detection_rate_min: 0.99, false_accept_max: 0.0 }
```

### Run lifecycle
`QUEUED → PREFLIGHT → RUNNING → COLLECTING → EVALUATING → COMPLETED | FAILED | CANCELLED`. Preflight verifies S1–S4, S6, calibration validity, Defender health.

### Execution modes
- **Individual run:** one scenario, one parameter set, N repetitions.
- **Batch:** list of (scenario, params, repetitions, noise profile); runs sequentially with a concurrency limit (default 1) and a shared seed hierarchy: `seed_run = HKDF(batch_seed, run_index)`.
- **Experiment:** batch + control group (benign traffic with identical timing) + evaluation configuration (see evaluation doc).

---

## 3. Scenarios

Every scenario lists: Purpose · Preconditions · Test setup · Attack procedure · Expected security event · Expected Defender classification · Expected response · Evidence to record · Pass criteria · Fail criteria. Common benign control: 5× as many legitimate requests, interleaved, from `alice`/`bob`, to measure false positives in the same run.

### Scenario 1 — Forgery of quantum-assisted verification evidence

| Field | Specification |
|---|---|
| **Purpose** | Test whether modified, fabricated, or unauthorised QVE is rejected. |
| **Preconditions** | Target ACTIVE; `alice` enrolled with $K_q$, $K_{req}$; backend `aer-noisy-lab-low`, calibration `VALID`; Defender in `BLOCKING` mode for resource `/transfer`. |
| **Test setup** | Generate legitimate request+QVE for `alice` (control). Capture it in the runner (simulating an eavesdropper who sees the evidence but not keys). |
| **Attack procedure** (variants, 100 trials each) | **F1** counts tampering: change counts for $k\in\{1,3,6\}$ settings by shifts of $\delta\in\{0.02,0.05,0.10\}$ in $\hat p$, keep MAC. **F2** MAC stripped/forged: random MAC. **F3** fabricated evidence from the *analytic ideal distribution* for guessed parameters (attacker lacks $K_q$). **F4** parameter swap: evidence for request A attached to request B. **F5** `execution_kind` falsification: claim `PHYSICAL_HARDWARE` with Aer data / no provider job id. **F6** stale calibration reference. |
| **Expected security event** | F1/F2: `evidence.mac_invalid`. F3: `evidence.params_mismatch`. F4: `evidence.params_mismatch`. F5: `evidence.provenance_invalid`. F6: `quantum.verification.inconclusive`. |
| **Expected classification** | `FORGERY` (all variants; F6 ⇒ `UNKNOWN`/`INCONCLUSIVE`). |
| **Expected response** | `BLOCK_REQUEST`; after ≥ 3 failures in 5 min from the same identity ⇒ `FLAG` + `OPEN_INCIDENT` (severity HIGH). |
| **Evidence to record** | request digest, QVE digest, which field modified, $X^2_{tot}$ and p-value where a statistical test ran, verdict, classification, response, latency (ingest → decision), backend descriptor. |
| **Pass** | Detection rate (classified `FORGERY` or rejected with any quantum/evidence event) ≥ 99% for F1(δ ≥ 0.05), F2–F5 = 100%; **0** forged requests accepted; benign false-reject rate ≤ 0.5% (95% UB ≤ 1%). |
| **Fail** | Any forged request accepted; classification missing; provenance falsification accepted; F1 with MAC valid but altered counts is accepted (it cannot be — MAC fails; test is that the MAC check precedes statistics). |

*Note:* F1 with δ small and a **valid MAC** is not an attacker capability without $K_q$. A variant **F1′ (insider with $K_q$, not a forgery of the evidence but a manipulation of the channel)** belongs to Scenario 4.

### Scenario 2 — Impersonation

| Field | Specification |
|---|---|
| **Purpose** | Test whether `mallory` can act as `alice` in the controlled environment. |
| **Preconditions** | `alice`, `bob`, `mallory` registered; keys distinct; `alice` has historical baseline of traffic (≥ 50 benign requests). |
| **Test setup** | Provide `mallory` with: (I-a) `alice`'s `key_id` only; (I-b) a captured valid request of `alice`; (I-c) `alice`'s *session cookie* (for human-facing endpoints) from a different IP/UA; (I-d) **stolen `alice` secret** — declared as **out-of-scope for prevention**, evaluated for behavioural detection only. |
| **Attack procedure** | I-a: sign with mallory's secret using alice's `key_id`. I-b: modify body, re-use headers. I-c: replay session cookie from different network context. I-d: perfectly signed requests with valid QVE but anomalous behaviour (new resource set, 10× rate, off-hours). |
| **Expected security event** | I-a/I-b: `signature.invalid` (+ `identity.mismatch` when `key_id` ≠ source principal fingerprint). I-c: `session.context_change`. I-d: `behaviour.anomaly`. |
| **Expected classification** | `IMPERSONATION`. |
| **Expected response** | I-a/I-b: `BLOCK_REQUEST`. I-c: `STEP_UP_VERIFICATION` (MFA) / `REVOKE_SESSION` if step-up failed. I-d: `FLAG` + `STEP_UP_VERIFICATION`; `QUARANTINE_IDENTITY` after sustained anomaly. |
| **Evidence to record** | claimed vs observed identity, key id, signature check outcome, source IP/UA fingerprint, anomaly score and contributing features, response, time to response. |
| **Pass** | I-a, I-b, I-c: 100% rejected or stepped-up; I-d: detection rate ≥ 80% at ≤ 2% benign FPR (this is an honest weaker target — behavioural detection, not cryptographic prevention); report with CI. |
| **Fail** | Any I-a/I-b accepted; I-d reported as "prevented" in documentation (it is detected, not prevented). |

### Scenario 3 — Replay

| Field | Specification |
|---|---|
| **Purpose** | Test reuse of previously captured valid requests and QVE. |
| **Preconditions** | Replay protection active (nonce store Redis + Postgres); clock skew 60 s; sandbox resource `/transfer` in `BLOCKING` mode. |
| **Requirements under test** | Nonce uniqueness per `(key_id, nonce)`; timestamp freshness ±60 s; request-bound QVE; duplicate `evidence_digest`; session binding; nonce TTL ≥ 300 s; Redis-flush recovery rule. |
| **Test setup** | Runner captures N=25 legitimate signed requests with QVE (via a tap on sandbox traffic). |
| **Attack procedure** | **R1** exact replay immediately (<1 s). **R2** exact replay after 5 s, 30 s (inside window) and 90 s, 400 s (outside window; also outside nonce TTL). **R3** replay with a fresh nonce but original signature. **R4** replay with fresh nonce and fresh timestamp but original QVE. **R5** replay the request but **swap** to a different `key_id`. **R6** Redis flush then replay of a request with timestamp inside the skew window of the flush (tests fail-closed rule). **R7** concurrent replay: 10 parallel identical requests (race on nonce claim). |
| **Expected security event** | R1/R2(≤60 s)/R7: `replay.detected`. R2(>60 s): `request.stale`. R3: `signature.invalid`. R4: `evidence.params_mismatch` (+ `replay.detected` of evidence if digest reused). R5: `signature.invalid`. R6: `replay.detected` or `request.stale` (fail-closed). |
| **Expected classification** | `REPLAY` (R1, R2, R4, R6, R7), `FORGERY` or `REPLAY` for R3 (primary label `REPLAY`; secondary allowed), `IMPERSONATION` for R5. |
| **Expected response** | `BLOCK_REQUEST`; ≥ 5 replays/min per key ⇒ `THROTTLE` + `OPEN_INCIDENT` (MEDIUM). |
| **Evidence to record** | original request id & time, replay delay, nonce, claim outcome, source of detection (Redis vs Postgres), race outcome for R7 (exactly one acceptance of the *original*, none for duplicates). |
| **Pass** | 0 replays accepted in all variants; R7: exactly 1 of 10 concurrent identical requests passes the nonce claim if the original was never processed, 0 if it was; detection classification correct ≥ 99%. |
| **Fail** | Any accepted replay; double-processing under race; Redis loss causes acceptance. |

### Scenario 4 — Quantum channel manipulation

| Field | Specification |
|---|---|
| **Purpose** | Test whether verification statistics detect controlled perturbations of the simulated quantum channel and distinguish them from legitimate noise. |
| **Preconditions** | Backend `aer-noisy-*`; calibration `VALID` for both circuit families; $m=24$, $N=1024$ per setting; $\alpha_{tot}=10^{-3}$. |
| **Test setup** | Baseline profile (`lab-low`, `lab-medium`) as the honest channel. Channel profile of the sandbox link is switched by the runner among manipulation models of Quantum §9.6. Control: honest channel at same noise (≥ 1 000 trials). |
| **Attack procedure** | Sweep: `intercept_resend_Z`, `intercept_resend_random` (fractions $f\in\{0.1,0.25,0.5,1\}$ of settings attacked); `over_rotation_Y(ε)`, `phase_kick(ε)` for $\varepsilon\in\{0.05,0.1,0.2,0.5\}$ rad; `depolarize(λ)` for $\lambda\in\{0.02,0.05,0.1,0.2\}$; `bellpair_decohere(v)` for $v\in\{0.95,0.8,0.6,0.4\}$ (teleport family). 200 trials per (model, intensity, noise profile). Also a **noise-drift control** (honest channel with increased noise ≤ $\kappa_{\min}$ tolerance) to measure the `INCONCLUSIVE`/`NOISE_DRIFT` path. |
| **Expected security event** | `quantum.channel.anomaly` with payload ($X^2_{tot}$, p-value, structure class); `quantum.verification.failed`. For drift: `quantum.calibration.drift`. |
| **Expected classification** | `CHANNEL_MANIPULATION` (FAIL); drift ⇒ `NOISE_DRIFT` (INCONCLUSIVE). |
| **Expected response** | `BLOCK_REQUEST` for FAIL on `BLOCKING`; `FLAG` and recalibration job for drift; `OPEN_INCIDENT` if ≥ 3 FAIL/5 min on a link. |
| **Evidence to record** | model, intensity, noise profile, per-setting counts, $X^2_s$, $X^2_{tot}$, p-values, $\hat\kappa_{x,y,z}$, direction errors, verdict, analytic power for the setting, backend descriptor, seeds. |
| **Pass** | (a) Honest-channel FRR ≤ 0.5% (95% UB ≤ 1%); (b) detection (FAIL) rate ≥ 99% for `intercept_resend_Z`, `intercept_resend_random` at $f\ge0.5$, `over_rotation_Y(ε≥0.2)`, `phase_kick(ε≥0.2)`; (c) detection rates for weaker intensities are **reported** with Wilson 95% CIs and compared with the analytic power prediction (agreement within CI); (d) every result displays `execution_kind`. |
| **Fail** | Any strong-manipulation class below target; honest FRR above bound; detection results not reproducible with the recorded seed; undocumented noise-budget limitation (depolarize λ within tolerance must be reported as *not detectable by design*, not hidden). |

### Scenario 5 — Conventional web-security testing (sandbox only)

All 5.x tests target the **sandbox target app**, run from the runner with curated payloads (S9), and expect the **Defender** to detect via its rule engine and the platform to remain unaffected. Note: the sandbox app is deliberately vulnerable *so that detection can be evaluated*; the *platform's own* endpoints are tested by the normal security test suite (SEC-* criteria), never by the Attack Lab.

#### 5.1 SQL injection

| Field | Specification |
|---|---|
| Purpose | Verify detection of SQLi attempts against sandbox `/search?q=` and `/login`. |
| Preconditions | Sandbox DB contains synthetic data only; sandbox app has vulnerable and hardened variants (`mode=vulnerable|hardened`). |
| Test setup | Reset sandbox DB; baseline benign traffic 500 requests. |
| Procedure | Payload corpus (fixed file, ≈ 40 entries): tautologies (`' OR '1'='1`), UNION probes (column-count discovery), comment truncation, stacked-query attempts, time-delay markers (limited to ≤ 2 s delay), error-based probes. Delivered via query, JSON body, header. Also encoded variants (URL-encoded, case-mixed) to test normalisation. |
| Expected event | `web.sqli.suspected` (from sandbox WAF-signal/telemetry + DB error spikes). |
| Classification | `WEB_SQLI`. |
| Response | `BLOCK_REQUEST` for the source principal on the sandbox resource; `OPEN_INCIDENT` if ≥ 5 attempts/min. |
| Evidence | payload id, encoding, endpoint, sandbox response code/time, DB error flag, detection rule id, latency. |
| Pass | Detection ≥ 95% on plain payloads, ≥ 80% on encoded variants (reported with CI); in `hardened` mode zero data returned and 0 successful injections; benign FPR ≤ 1% on 500 benign queries including apostrophes (e.g. "O'Brien"). |
| Fail | Benign names blocked > 1%; any successful data extraction in `hardened` mode. |

#### 5.2 Cross-site scripting

| Field | Specification |
|---|---|
| Purpose | Verify detection of reflected/stored XSS attempts and that the Defender UI is itself not vulnerable to attack content. |
| Preconditions | Sandbox comment endpoint stores raw input in `vulnerable` mode. |
| Setup | Corpus ≈ 30 payloads: `<script>` tags, event handlers (`onerror`), `javascript:` URLs, SVG vectors, attribute-breaking, encoded variants. |
| Procedure | Submit to comment/search endpoints; fetch rendered pages with a headless browser inside the lab zone to check execution in the sandbox page. |
| Expected event | `web.xss.suspected`; additionally, **the Defender UI renders the captured payload as text** (no execution). |
| Classification | `WEB_XSS`. |
| Response | `FLAG`; `BLOCK_REQUEST` for repeat offenders. |
| Evidence | payload id, context (reflected/stored), browser execution flag in sandbox, CSP violation reports, Defender UI render check result. |
| Pass | Detection ≥ 95% plain, ≥ 80% encoded; **0** executions in the Defender UI (browser test); `hardened` mode: 0 executions in sandbox. |
| Fail | Any script execution in the Defender UI (critical defect). |

#### 5.3 Authentication weaknesses

| Field | Specification |
|---|---|
| Purpose | Detect credential attacks and weak-auth patterns against sandbox `/login`. |
| Preconditions | 20 synthetic accounts, sandbox passwords from a synthetic list; sandbox variants `weak` (no throttling, no lockout) and `hardened`. |
| Procedure | **A1** brute force on one account (≤ 300 tries); **A2** credential stuffing (≤ 500 synthetic pairs across accounts); **A3** user enumeration via response/timing differences; **A4** session fixation attempt; **A5** default/weak-password probe from synthetic list. |
| Expected event | `auth.failed` burst; `auth.enumeration.suspected`; `session.anomaly`. |
| Classification | `AUTH_ABUSE`. |
| Response | `THROTTLE` then `QUARANTINE_IDENTITY` (source), `FLAG` for enumeration. |
| Evidence | attempts/min, distinct accounts targeted, success flag (in `weak` mode), time to first detection, response timestamp. |
| Pass | Detection of A1/A2 within ≤ 10 attempts / 30 s (median); A3 detection ≥ 80%; `hardened`: 0 successful authentications by attacker; benign mistyped-password users not blocked (FPR ≤ 1%). |
| Fail | Detection after > 50 attempts; benign lockouts > 1%. |

#### 5.4 Rate-limit failures

| Field | Specification |
|---|---|
| Purpose | Check that rate-limit abuse is detected and the Defender's own limits hold. |
| Preconditions | Sandbox `/api/orders` with limit 60/min (`enabled`), and a `disabled` variant. |
| Procedure | **L1** constant overload at 5× limit (≤ 20 rps cap, S6); **L2** burst/low-and-slow (just under limit, long duration); **L3** distributed identities (3 synthetic principals sharing a source); **L4** header spoofing attempt (`X-Forwarded-For` rotation). |
| Expected event | `ratelimit.exceeded`; `behaviour.anomaly` for L2/L3. |
| Classification | `RATE_ABUSE`. |
| Response | `THROTTLE`; `BLOCK_REQUEST` after sustained abuse. |
| Evidence | rps profile, limiter decisions, 429 counts, bypass flag (L4), detection latency. |
| Pass | L1 429s ≥ 95% of excess requests; L4 bypass = 0 (limiter keys on authenticated principal and trusted proxy chain); L2/L3 detection ≥ 70% (reported). |
| Fail | Bypass via spoofed header. |

#### 5.5 Input validation failures

| Field | Specification |
|---|---|
| Purpose | Verify handling of malformed and boundary inputs by the sandbox and detection of fuzzing. |
| Procedure | Oversized bodies (up to 2 MiB), deep JSON (depth 50), wrong types, unknown fields, unicode/normalisation edge cases, negative/NaN numbers (for quantum parameters: θ outside $[0,\pi]$, shots above limit) sent to sandbox and to the **platform's own** `/ingest` through the signed path to check 422/413 responses. |
| Expected event | `input.invalid` with reason code; repeated ⇒ `input.fuzzing.suspected`. |
| Classification | `INPUT_ABUSE`. |
| Response | `LOG_ONLY` for single events; `THROTTLE` for bursts. |
| Evidence | payload class, status code, validation error code, stack-trace absence check. |
| Pass | 100% of invalid inputs rejected with 4xx and no stack trace/SQL text; 0 server 5xx from validation paths; fuzz-burst detection ≥ 90%. |
| Fail | Any 5xx, any exception text in the response, any invalid quantum parameter reaching the worker. |

---

## 4. Evidence and reporting recorded per run

`attack_runs` (config, seed, versions) · `attack_run_steps` (step index, request summary, response status, timing) · `evidence_artifacts` (hashes of captured material, never secrets) · Defender-side detections and responses (read via the evaluation join) · safety checks log · environment snapshot (Qiskit/Aer versions, noise-model hash, calibration id).

## 5. Acceptance criteria for the Attack Lab

| ID | Criterion |
|---|---|
| LAB-1 | A run against an unregistered or expired target is refused with `403` and a `lab.safety.violation` event, before any packet is sent. |
| LAB-2 | A network test from the runner container to a public IP and to a non-registered private port fails (firewall) and is logged. |
| LAB-3 | Cancel stops an in-flight batch within 5 s and leaves the sandbox in a reset state. |
| LAB-4 | Re-running a scenario with the same `config_hash` and seed reproduces the same attack inputs byte-for-byte; quantum counts reproduce exactly on the ideal/noisy simulator when the seed is fixed. |
| LAB-5 | Each of Scenarios 1–5 has a scenario file, unit tests of the attack generator, and an integration test that checks the expected event/classification/response chain end to end. |
| LAB-6 | Ground-truth labels are inaccessible to the detection role (ARC-3) and appear in reports only via the evaluation service. |
| LAB-7 | Every Scenario 4 report prints the noise-budget statement and the `execution_kind` for every datapoint. |
