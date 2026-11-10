# QuantumShield — Frontend Application Specification

**Status:** Specification v1.0, written before any code exists. Nothing here has been implemented or tested; the repository has not been created.
**Applies to:** `apps/defender-web` (QuantumShield Defender) and `apps/attack-lab-web` (QuantumShield Attack Lab), plus shared `packages/ui` and `packages/api-client`.
**Normative sources:** `api/api-contracts-and-schema.md` (endpoints, enums, envelopes), `security/hybrid-security-architecture.md` (sessions, CSRF, CSP), `architecture/system-architecture.md`, `evaluation/detection-and-evaluation.md`, `security/attack-lab-methodology.md`. This document **supersedes Appendix A** of `development/antigravity_implementation_backlog.md` where they differ (this file adds `/threats` and `/settings` for the Defender and splits the Lab run pages).

Tags used below: **[MVP]** required for v1.0 · **[V1.1]** planned next · **[Future]** not in v1.

---

## 0. Ground rules, clarifications and API gaps

### 0.1 Rules that apply to every page
1. **No invented endpoints.** Pages call only endpoints in API doc §3 (or §0.3 addenda once accepted). If a needed endpoint is missing, the page is built against a documented mock and the gap is listed in §0.3.
2. **The frontend makes no security decisions.** Hiding a control is UX; every action is re-authorised by the API.
3. **Every quantum datum shows its `execution_kind` badge** (`IDEAL_SIMULATOR`, `NOISY_SIMULATOR`, `PHYSICAL_HARDWARE`). A shared component (`QuantumDatum`) enforces it.
4. **Honesty footnote** on every page that shows quantum data: *"Simulation results. The quantum layer is an additive verification experiment; it does not secure HTTP traffic or databases."*
5. **Attacker-controlled strings** (event payloads, User-Agent, sandbox inputs, payload corpora) render only through `SafeText` (§6.5).
6. **PASS, FAIL and INCONCLUSIVE are always distinct** in colour, icon and text; INCONCLUSIVE is never counted as PASS in any tile or chart.
7. **Every rate shows `n`**, and evaluation rates also show a 95% confidence interval.

### 0.2 Clarifications that amend earlier documents (to be recorded as ADR-FE-001)
| # | Earlier statement | Problem | Resolution used here |
|---|---|---|---|
| C1 | Backlog P6-01: "`middleware.ts` … redirects unauthenticated users" | Session cookies are `__Host-` cookies issued by `api.<domain>`; they are **not sent to** `defender.<domain>` / `lab.<domain>`, so Next.js middleware cannot see them. | Route protection is **client-side** (`AuthGate`, §6.4) using `GET /auth/me`; real enforcement is server-side in the API. Middleware is used only for the CSP nonce and security headers. |
| C2 | Earlier Security doc §4 described double-submit with a non-HttpOnly `qs_csrf` cookie. | A cookie scoped to the API host cannot be read by JavaScript on the separate app origins; duplicating the token in a cookie creates two sources of truth. | **Normative MVP decision:** use a session-bound synchronizer token. Return `csrf_token` in the JSON body of `POST /auth/login` and `GET /auth/me`; keep it in frontend memory only; send `X-CSRF-Token` on mutating browser requests. The API validates it against the active session using a server-held HMAC secret and constant-time comparison, and independently checks exact `Origin`. Do not set a `qs_csrf` cookie. Record this decision in `docs/development/adr/ADR-FE-001-csrf-token-transport.md`. |

### 0.3 Required API addenda (do not build UI against these until accepted)
| ID | Gap | Needed by | Interim behaviour |
|---|---|---|---|
| G-1 | `/metrics/overview` has no response schema or `window` parameter; dashboards need verdict time series, classification counts, blocked count. | D-02, D-06 | Define `GET /metrics/overview?window=1h\|24h\|7d` returning counters + hourly series. Until then, derive counters from `GET /events` pages (slow, capped at 24 h). |
| G-2 | No endpoints for TOTP enrolment/disable, password change, user listing. | D-11, D-01 | MFA enrolment and user admin are **[V1.1]**; MVP settings are read-only for profile and exclude user management. |
| G-3 | No `GET /lab/batches/{id}` and no `GET /lab/experiments` list. | L-05, L-09 | Poll `GET /lab/runs` filtered client-side by `batch_id`/`experiment_id`; experiments list is held in client state after creation until the endpoint exists. |
| G-4 | `/lab/runs` list filters (`status`, `scenario_id`, `batch_id`, `after`) not specified. | L-01, L-06 | Use the normative cursor pagination and filters defined in API contract §3.8. |
| G-5 | `GET /lab/scenarios/{id}` must return a JSON-Schema (`parameters_schema`) for dynamic forms. | L-03 | Use the normative `parameters_schema` JSON Schema returned by `GET /lab/scenarios/{scenario_id}`; server-side validation remains authoritative. |
| G-6 | Report export (PDF/Markdown file) not defined. | D-10, L-10 | **[MVP]** use the normative `GET /reports/{report_id}/export?format=json|markdown` API contract; PDF **[Future]**. |
| G-7 | No endpoint listing recent quantum verifications. | D-04 | Use `GET /quantum/verifications` for the recent-verification list and `GET /quantum/verifications/{request_id}` for details. |

---

## 1. Shared patterns

### 1.1 Application shell
- **Header (56 px):** product name + app badge ("Defender" / "Attack Lab"), environment tag (`local`/`staging`/`prod`), global **live-connection indicator** (green "Live", amber "Reconnecting", grey "Paused"), notification bell, user menu (profile, role, logout).
- **Sidebar (240 px, collapsible to 64 px):** grouped navigation with icons + labels, active-route highlight, permission-filtered items.
- **Content area:** page header (title, breadcrumbs, primary actions), filter bar when applicable, content.
- **Footer strip (only quantum pages):** honesty footnote.

### 1.2 State templates (used by every page; pages list only deviations)
| State | Component | Behaviour |
|---|---|---|
| Loading (first load) | `TableSkeleton`, `CardSkeleton`, `ChartSkeleton` | Skeleton matching final layout; no spinner-only screens; shown after 150 ms to avoid flicker. |
| Refreshing | thin top progress bar + stale-data timestamp | Previous data stays visible. |
| Empty | `EmptyState` (icon, one-line explanation, primary action if permitted) | Distinguishes "no data yet" from "no results for filters" (the latter has "Clear filters"). |
| Error | `ErrorPanel` | Shows problem+json `title` and `detail`, `request_id`, "Retry". 401 → login redirect, 403 → `ForbiddenPanel`, 404 → `NotFoundPanel`, 429 → countdown from `Retry-After`, 503 → degraded banner. Never raw server text, never stack traces. |
| Degraded realtime | `ConnectionBanner` | "Live updates paused — showing data as of HH:MM:SS" with Reconnect button. |

### 1.3 Realtime conventions
Single `WsClient` per app (§6.6). Channel→page map: `events` (D-02, D-05, D-06), `incidents` (D-02, D-07), `quantum` (D-04, D-09), `responses` (D-08), `system` (D-11), `lab.runs` (L-01, L-05, L-06, L-07). Events carry `seq`; duplicates are dropped; gaps trigger REST resume.

### 1.4 Permission mapping (from Security doc §3)
`PermissionGate perm="incidents:write"` renders children or a disabled/hidden control (per prop). Roles: `admin`, `security_analyst`, `viewer`, `lab_operator`, `lab_viewer`, `auditor`.

### 1.5 Page specification template
Defender pages use: Purpose · Layout & navigation · UI components · Data displayed · API endpoints · User interactions · Permissions · Loading · Empty · Error · Real-time · Acceptance. Attack Lab pages use: Purpose · Layout · UI components · API dependencies · User actions · Execution states · Error handling · Authorization · Acceptance. Acceptance IDs: `FE-D<page>-<n>` and `FE-L<page>-<n>`; each is a testable assertion.

---

## 2. QuantumShield Defender (`apps/defender-web`, port 3000)

### 2.0 Navigation map
```text
Overview            /                          D-02
Live Events         /events                    D-05
Threats             /threats                   D-06
Incidents           /incidents                 D-07
Responses           /responses                 D-08
Resources           /resources                 D-03
Quantum
  ├ Verification    /quantum/verification      D-04
  └ Backends & Jobs /quantum/backends          D-09
Reports             /reports                   D-10
System              /health, /settings         D-11
(auth)              /login, /login/mfa         D-01
```

### D-01 Login and authentication  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Authenticate operators; complete MFA; end sessions safely. |
| Layout & navigation | Centered card, no sidebar. Routes `/login`, `/login/mfa`. After success redirect to validated return path or `/`. |
| UI components | `LoginForm` (email, password with show/hide), `MfaForm` (6-digit TOTP, autofocus, paste-friendly), `SessionExpiredBanner`, `ExecutionKindFooter` not shown. |
| Data displayed | None except inline validation and generic error. |
| API endpoints | `POST /auth/login` (`app: "defender"`), `POST /auth/mfa/verify`, `GET /auth/me`, `POST /auth/logout`. |
| User interactions | Submit with Enter; toggle password visibility; logout from user menu (also invoked on idle warning). |
| Permissions | Public route; all others require a valid session. |
| Loading | Submit button disabled with spinner; fields retained. |
| Empty | n/a |
| Error | 401: single message "Email or password is incorrect" (never reveals which). MFA failure: "Code is invalid or expired". 429: disabled form with countdown from `Retry-After`. 422: field-level. 503: banner "Service unavailable". |
| Real-time | None. Idle warning at 25 min of inactivity (session idle limit is 30 min) with "Stay signed in" calling `GET /auth/me`. |
| Acceptance | **FE-D01-1** successful login reaches `/`; **-2** unknown-user and wrong-password produce byte-identical UI text; **-3** 429 shows countdown and re-enables at 0; **-4** return-path open-redirect cases (`https://evil`, `//evil`, `javascript:`) are rejected, only relative in-app paths accepted; **-5** after login `localStorage` and `sessionStorage` contain no token or CSRF value (Playwright assertion); **-6** password never kept in component state after submit; **-7** axe: 0 serious/critical violations. |

### D-02 Main security dashboard  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | At-a-glance posture and entry point to investigation. |
| Layout & navigation | Page title "Overview". Row 1: KPI tiles. Row 2 (2 columns): "Verification verdicts" chart · "Events by classification" chart. Row 3 (2 columns): "Open incidents" · "Live events (last 20)". Right rail card: "Quantum status". |
| UI components | `KpiTile` ×6 (open incidents by severity, events/min, blocked requests 24 h, verification FAIL rate, INCONCLUSIVE rate, active backend), `VerdictChart`, `ClassificationChart`, `IncidentList`, `LiveEventMini`, `QuantumStatusCard` (backend badge, calibration age/validity, queue depth), `TimeWindowSelect` (1 h/24 h/7 d). |
| Data displayed | Counters and series per G-1; open incidents (title, severity, count, last seen); latest events; backend descriptor and calibration status. Every rate shows numerator/denominator. |
| API endpoints | `GET /metrics/overview` (G-1), `GET /incidents?status=OPEN&limit=10`, `GET /events?limit=20`, `GET /quantum/backends`, `GET /quantum/calibrations?limit=1`, WS `events,incidents,quantum`. |
| User interactions | Change window; click tile/chart segment → navigates to `/events` or `/incidents` with matching filters pre-applied; click incident → `/incidents/[id]`. |
| Permissions | `events:read`, `incidents:read`, `quantum:read` (tiles for missing permissions are hidden). |
| Loading | Skeleton tiles/charts; each card loads independently. |
| Empty | "No events in this window" with hint to register a protected resource (link if `resources:write`). |
| Error | Per-card `ErrorPanel` so one failing source does not blank the page. |
| Real-time | Events/min and live list update from WS; counters refresh on each `incident.*` and every 30 s via query refetch; stale indicator if > 60 s. |
| Acceptance | **FE-D02-1** tiles match the API values for a seeded fixture (component test with MSW); **-2** a WS `security_event.created` appears in the mini stream in < 1 s (Playwright with real local stack); **-3** INCONCLUSIVE rate is a separate tile, never merged; **-4** clicking a chart segment applies the identical filter in the destination URL; **-5** cards degrade independently when one endpoint returns 503; **-6** tile permission gating verified for `viewer`. |

### D-03 Protected resource management  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Register protected apps/resources, set enforcement mode, manage signing/quantum credentials. |
| Layout & navigation | `/resources` table; `/resources/new` form; `/resources/[id]` tabs: Overview · Credentials · Allowed backends · Recent events. |
| UI components | `ResourceTable`, `ResourceForm` (name, base URL, enforcement mode, sandbox flag read-only after creation, allowed backends multi-select), `EnforcementModeToggle` with confirmation, `CredentialPanel` (list of key ids with status/expiry; Issue / Rotate / Revoke), `OneTimeSecretDialog`. |
| Data displayed | name, status, `enforcement_mode` (BLOCKING/MONITOR with explanatory tooltip: "BLOCKING fails closed on timeout"), `is_sandbox`, allowed backends, credential `key_id`s (never secrets), recent events. |
| API endpoints | `GET/POST /resources`, `GET/PATCH /resources/{id}`, `POST /resources/{id}/credentials`, rotate and revoke sub-routes under credentials (API doc §3.2), `GET /events?resource_id=`. |
| User interactions | Create/edit; switch enforcement mode (confirm dialog); issue credential → secret shown **once** in `OneTimeSecretDialog` with Copy; rotate (shows overlap window notice); revoke (typed confirmation of key id). |
| Permissions | read: `resources:read`; write/credentials: `resources:write` (admin). Others see read-only. |
| Loading / Empty / Error | Table skeleton; empty: "No protected resources yet" + "Register resource"; 409 on duplicate name shown on the field; 404 for other-org ids shows `NotFoundPanel`. |
| Real-time | None required; recent-events tab uses the live stream filtered by resource. |
| Acceptance | **FE-D03-1** secret shown once, cleared from React state and DOM when dialog closes (test inspects store/DOM); **-2** secret never in URL, storage, logs (Playwright console + storage scan); **-3** changing to MONITOR requires confirmation; **-4** viewer sees no write controls; **-5** validation messages map to fields from `errors[].loc`. |

### D-04 Quantum verification monitoring  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Inspect quantum verification outcomes and their statistical evidence. |
| Layout & navigation | `/quantum/verification`: top filter bar (verdict, family `direct\|teleport`, backend, resource, time) · verdict trend chart · results table. Detail route `/quantum/verification/[requestId]`. |
| UI components | `VerdictChart` (PASS/FAIL/INCONCLUSIVE stacked), `VerificationTable`, `VerificationDetail` (aggregate card: `x2_total`, `dof`, `p_value`, `alpha`, `max_abs_z` vs threshold; per-setting table with θ, φ, basis, counts, expected p, z, test used; `StructurePanel` with κ per axis and direction error; `BlochPlot` of expected vs observed), `BackendBadge`, `CalibrationLink`. |
| Data displayed | Fields from API doc §4 final response (`quantum.verdict`, `settings`, `shots_per_setting`, `aggregate`, `structure`, `calibration_id`, `backend`). |
| API endpoints | `GET /events` (types `quantum.verification.*`, G-7), `GET /quantum/verifications/{request_id}`, `GET /quantum/calibrations`, WS `quantum`. |
| User interactions | Filter/sort; open detail; toggle "show settings used for χ² vs exact test"; copy request id; link to related event/incident. |
| Permissions | `quantum:read`. |
| Loading / Empty / Error | Detail skeleton with fixed section heights; empty: "No verifications yet"; 404: "Verification not found or not visible"; if `statistics` missing for INCONCLUSIVE, show the precondition reason instead of empty charts. |
| Real-time | `quantum.verdict` messages prepend rows (respecting active filters); counters update. |
| Acceptance | **FE-D04-1** every row/card shows `execution_kind` badge (test fails if absent); **-2** INCONCLUSIVE rows display reason (e.g., `calibration STALE`) and distinct style; **-3** detail view renders all aggregate fields from a fixture exactly (snapshot of values, not styling); **-4** noise-budget note displayed whenever structure class is `NOISE_DRIFT` or `CONSISTENT` ("isotropic contraction within tolerance is accepted by design"); **-5** per-setting table shows which test (χ² or exact) was used. |

### D-05 Live security event stream  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Real-time monitoring and triage of security events. |
| Layout & navigation | `/events`: filter bar · stream controls (Pause/Resume, auto-scroll toggle, density) · virtualised table · right detail drawer (or `/events/[id]`). |
| UI components | `EventTable` (columns: time, severity, event type, classification, resource, source IP, summary, response), `EventFilters` (type, severity, classification, resource, time range, free-text on summary), `EventDrawer`, `SeverityBadge`, `ClassificationBadge`, `ResponseChip`, `PauseBuffer` (shows "N new events"). |
| Data displayed | Event fields per API doc §6 envelope and `GET /events/{id}`; payload JSON pretty-printed **as text** with a 20 KB cap and "Show more". |
| API endpoints | `GET /events` (filters `type,severity,classification,resource_id,from,to,after_seq`), `GET /events/{id}`, WS `events`. |
| User interactions | Filter (state in URL), pause (buffers up to 2000, then drops oldest with notice), resume (flush), open drawer, copy event id, "Open related incident". |
| Permissions | `events:read` (viewer, analyst, admin, auditor). |
| Loading / Empty / Error | Skeleton rows; empty states distinguish "no events yet" vs "no matches"; REST failure keeps WS rows visible with banner. |
| Real-time | Ordered by `seq`; client dedups; on reconnect resumes with `after_seq`; if gap > 1000 the table reloads and shows "Resynced". |
| Acceptance | **FE-D05-1** exactly-once rendering across a simulated 10 s disconnect (ARC-6 client side); **-2** 5 000 events/min fixture keeps UI responsive (main-thread long tasks < 100 ms in Playwright trace) via virtualisation; **-3** payload `<script>alert(1)</script>` renders as text and does not execute; **-4** filters round-trip through URL; **-5** Pause stops visible changes within one frame and counts buffered events. |

### D-06 Threat detection and classification  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | See what was detected, how it was classified, and why (rules and confidence). |
| Layout & navigation | `/threats`: classification summary cards (FORGERY, REPLAY, IMPERSONATION, CHANNEL_MANIPULATION, WEB_SQLI, WEB_XSS, AUTH_ABUSE, RATE_ABUSE, INPUT_ABUSE, NOISE_DRIFT, UNKNOWN) · trend chart · detections table · explanation drawer. |
| UI components | `ClassificationCard` (count, trend, top resource), `DetectionTable`, `DetectionDrawer` (primary classification, confidence, **contributing rule ids**, precedence explanation, evidence summary, linked event/incident), `PrecedenceLegend`. |
| Data displayed | Detection fields: `classification`, `confidence`, `rule_ids`, `features` (as formatted text), `detector_version`; events grouped by classification. |
| API endpoints | `GET /events?classification=…` (detection data embedded per API doc event/detection shape), `GET /events/{id}`, `GET /metrics/overview` (G-1). |
| User interactions | Click card to filter; open drawer; jump to incident; filter by confidence range and rule id. |
| Permissions | `events:read`. |
| Loading / Empty / Error | As §1.2; empty: "No detections in this window"; unknown classification values from the API render as `UNKNOWN` with raw value in tooltip (forward compatible). |
| Real-time | Counts update from WS `events`. |
| Acceptance | **FE-D06-1** all 12 classification enum values have a card, label and colour (test iterates the generated enum); **-2** drawer shows rule ids and confidence for fixture detections; **-3** behavioural IMPERSONATION shows "behavioural — not a cryptographic finding" note; **-4** `NOISE_DRIFT` card labelled "informational — triggers recalibration". |

### D-07 Incident management  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Triage, investigate and close incidents. |
| Layout & navigation | `/incidents` list with status tabs (Open, Investigating, Contained, Resolved, False positive); `/incidents/[id]` with header (title, severity, status, assignee), timeline, events, responses, notes, evidence panel. |
| UI components | `IncidentTable`, `StatusStepper`, `IncidentTimeline`, `NoteEditor` (plain text, 4 000 chars), `AssigneeSelect` (current user or "unassigned" in MVP), `EvidencePanel` (digests only), `ResponseActionsPanel`. |
| Data displayed | incident fields (§9.4 DDL), correlated events, related `response_actions`, notes with authors, `sandbox=true` label when applicable. |
| API endpoints | `GET /incidents`, `GET /incidents/{id}`, `PATCH /incidents/{id}`, `POST /incidents/{id}/notes`, `GET /responses`, WS `incidents`. |
| User interactions | Change status (RESOLVED and FALSE_POSITIVE require a note — enforced in UI and server), add note, assign to self, jump to events, trigger manual response (D-08). |
| Permissions | read: `incidents:read`; write: `incidents:write` (analyst, admin). Auditor/viewer read-only. |
| Loading / Empty / Error | Skeletons; empty: "No incidents"; 409 on invalid transition shows server `detail` inline and reverts the optimistic update. |
| Real-time | `incident.created\|updated` update list/detail live; concurrent edit conflict banner if `updated_at` changed under the user. |
| Acceptance | **FE-D07-1** invalid transitions disabled in UI and server 409 handled; **-2** resolve without note blocked client-side and server-side; **-3** live update appears within 1 s; **-4** read-only role has no mutation controls; **-5** notes rendered via `SafeText`. |

### D-08 Response action management  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Review automatic actions, execute and revert manual actions, review the response policy. |
| Layout & navigation | `/responses`: tabs "History" · "Policy". History table with filters; "New manual action" button. |
| UI components | `ResponseTable` (action, target, mode AUTO/MANUAL, status, reason, executed by, expires, reverted), `ManualActionDialog` (action select, target, reason ≥ 10 chars, duration), `PolicyTable` (read-only matrix from Evaluation §2 data), `DryRunBadge`. |
| Data displayed | `response_actions` fields; policy rows and `dry_run` state. |
| API endpoints | `GET /responses`, `POST /responses`, `GET /response-policies`, `PUT /response-policies/{id}` **[V1.1 UI edit]**, WS `responses`. |
| User interactions | Filter history; create manual action; (admin) toggle dry-run **[V1.1]**; view expiry countdown. |
| Permissions | history: `incidents:read`; manual action: `responses:execute` (analyst, admin); policy edit: admin. |
| Loading / Empty / Error | Skeletons; empty "No response actions"; 409 from safeguards (e.g., would block an admin session, rate cap) shown verbatim as `detail`. |
| Real-time | `response.executed` rows appear live. |
| Acceptance | **FE-D08-1** reason < 10 chars blocked; **-2** safeguard 409 displayed without UI crash; **-3** AUTO vs MANUAL visually distinct; **-4** expiry countdown accurate to ±1 s in a fake-timer test; **-5** viewer cannot see "New manual action". |

### D-09 Quantum backend and job status  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Operate the quantum plane: backends, calibration, jobs. |
| Layout & navigation | `/quantum/backends`: backend cards · calibration table · jobs table; `/quantum/jobs/[id]` detail. |
| UI components | `BackendCard` (id, `ExecutionKindBadge`, provider, noise-model hash short form, health, n_qubits, dynamic-circuit support), `CalibrationTable` (family, status VALID/STALE/REJECTED, valid-until, windows, shots), `JobTable` (status chips for all `JobStatus` values, attempts, duration), `JobDetail` (spec, per-circuit results, error), `CalibrateButton`, `CancelJobButton`. |
| Data displayed | `GET /quantum/backends` descriptors; calibration records; job fields (API doc §5). |
| API endpoints | `GET /quantum/backends`, `GET/POST /quantum/calibrations`, `GET /quantum/jobs/{id}`, `POST /quantum/jobs`, `POST /quantum/jobs/{id}/cancel`, WS `quantum`. (No job-list endpoint exists in API doc §3.2; the table shows jobs observed via WS `quantum.job.updated` and events, and jobs fetched by id. See G-8 below.) |
| User interactions | Start calibration (analyst/admin) with backend + family + profile; cancel running job; open job detail; refresh. |
| Permissions | read `quantum:read`; calibrate `quantum:calibrate`; cancel/create per API. |
| Loading / Empty / Error | Skeletons; empty jobs: "No jobs yet"; hardware backend absent: card reads "Physical hardware: not available in v1"; STALE calibration shows banner "Verification will return INCONCLUSIVE until recalibrated". |
| Real-time | `quantum.job.updated` updates status chips live. |
| Acceptance | **FE-D09-1** all eight `JobStatus` values have labels/colours (enum iteration test); **-2** no component can label a backend with `provider='qiskit-aer'` as hardware (type-level + test); **-3** cancel button only for `QUEUED\|RUNNING`; **-4** STALE calibration warning visible. |

> **G-8 (additional gap):** a `GET /quantum/jobs` list endpoint is not in API doc §3.2. The MVP job table is session-local (WS + fetch-by-id); requesting the list endpoint is recommended.

### D-10 Evaluation reports and analytics  **[MVP: viewer; generation in Lab]**
| Field | Specification |
|---|---|
| Purpose | Read evaluation reports and detection-quality analytics. |
| Layout & navigation | `/reports` list (kind, created, runs, execution kinds) · `/reports/[id]` viewer with sections matching Evaluation §4.6. |
| UI components | `ReportTable`, `ReportViewer`, `MetricWithCI` (value, CI, n), `ConfusionMatrix`, `LatencyBoxplot`, `RocChart` (when present), `LimitationsSection` (mandatory), `ReproBlock` (config hash, seeds, versions, git SHA), `DownloadMenu` (JSON, Markdown; G-6). |
| Data displayed | `evaluation_reports.metrics`, `config`, `environment`, `execution_kinds`. |
| API endpoints | `GET /reports`, `GET /reports/{id}`, (create from Lab: `POST /reports`). |
| User interactions | Filter by kind/date; open; download; copy config hash. |
| Permissions | `reports:read`; creation in the Lab requires `reports:create`. |
| Loading / Empty / Error | Skeleton; empty "No reports yet — run an experiment in the Attack Lab"; report lacking limitations/noise-budget section renders an `InvalidReportPanel` instead of data. |
| Real-time | None. |
| Acceptance | **FE-D10-1** every rate rendered with n and CI (component test scans for bare percentages); **-2** report without limitations section is refused; **-3** mixed `execution_kind` data is shown stratified, never pooled; **-4** downloaded JSON is byte-identical to the API response. |

### D-11 System health and settings  **[MVP: health + read-only settings]**
| Field | Specification |
|---|---|
| Purpose | Dependency health and read-only operator settings. |
| Layout & navigation | `/health` grid; `/settings` tabs: Profile · Session · Response policy (read-only) · About. |
| UI components | `HealthGrid` (API, PostgreSQL, Redis, worker heartbeat, scheduler, WebSocket clients, rate limiter), `ProfileCard`, `SessionCard` (expiry countdown), `PolicyTable` (read-only), `AboutCard` (versions, honesty statements from Security §1 / Quantum §11). |
| Data displayed | `/health/ready` details (admin only), `/auth/me` profile and permissions, policy rows. |
| API endpoints | `GET /health`, `GET /health/ready`, `GET /auth/me`, `GET /response-policies`, WS `system`. User admin/MFA enrolment: **[V1.1]** pending G-2. |
| User interactions | Refresh; view permissions; logout. |
| Permissions | `/health` summary: any role; detailed dependency list: admin; settings: any authenticated role. |
| Loading / Empty / Error | Skeleton tiles; readiness failure shows red tile with dependency name and `request_id`. |
| Real-time | `system.health` and `system.degraded` events update tiles; global banner when any dependency is red. |
| Acceptance | **FE-D11-1** `system.degraded` event shows the global banner within 1 s; **-2** non-admin does not see dependency internals; **-3** About tab contains the exact honesty statements; **-4** session countdown reflects `session_expires_at`. |


---

## 3. QuantumShield Attack Lab (`apps/attack-lab-web`, port 3001)

The Attack Lab is a **separate Next.js application** with its own session cookie (`__Host-qs_lab_sid`), its own deployment (`lab.<domain>`), and a persistent **safety banner** ("Authorised sandbox testing only · synthetic data · targets: registered sandboxes only"). It shares design tokens and `packages/ui` with the Defender but never imports Defender feature code.

### 3.0 Navigation map and run states
```text
Dashboard            /                         L-01
Scenarios            /scenarios                L-02
  └ Configure        /scenarios/[id]           L-03
New run              /runs/new                 L-04 (single)
New batch            /batches/new              L-05
Runs                 /runs, /runs/[id]         L-06
  ├ Logs             /runs/[id]/logs           L-07
  └ Results          /runs/[id]/results        L-08
Compare              /experiments, /experiments/[id]   L-09
Reports              /reports, /reports/new    L-10
Targets              /targets                  L-11
Kill switch (admin)  /kill-switch              L-11
```

**Run status presentation (`RunStatus`, API doc §1):**
| Status | Icon / colour | Meaning for the user | Allowed actions |
|---|---|---|---|
| QUEUED | clock / grey | Waiting for runner | Cancel |
| PREFLIGHT | shield-check / blue | Safety checks S1–S4, S6, calibration, Defender health | Cancel |
| RUNNING | play / blue | Attack steps executing | Cancel |
| COLLECTING | download / blue | Gathering telemetry | Cancel |
| EVALUATING | calculator / blue | Joining ground truth with detections | — |
| COMPLETED | check / green | Results available | View results, Report |
| FAILED | x-octagon / red | Runner or safety failure; sandbox reset queued | View logs |
| CANCELLED | ban / amber | Stopped by user or kill switch | View logs |

All states have a text label; colour is never the only signal.

### L-01 Attack Lab dashboard  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Overview of lab activity, safety posture and scenario coverage. |
| Layout | Row 1: Safety status card · Active runs card · Last 24 h summary. Row 2: Scenario coverage matrix (scenario × last result). Row 3: Recent runs table. |
| UI components | `SafetyStatusCard` (kill-switch state, active targets, targets expiring ≤ 7 days), `ActiveRunsCard`, `CoverageMatrix` (cell = last run status + detection rate with n), `RecentRunsTable`, `QuickStartMenu`. |
| API dependencies | `GET /lab/runs` (G-4), `GET /lab/targets`, `GET /lab/scenarios`, WS `lab.runs`. |
| User actions | Start new run/batch; open run; open scenario; view expiring targets. |
| Execution states | Active runs show status chip and progress (steps/total). |
| Error handling | Per-card errors; if `GET /lab/targets` fails, the "Start run" buttons are disabled with explanation (cannot verify safety). |
| Authorization | Read: `lab:runs:read` (lab_viewer, lab_operator, analyst, auditor, admin). Start actions: `lab:runs:execute`. |
| Acceptance | **FE-L01-1** with kill switch active, dashboard shows a prominent red "Kill switch ON" and disables all start actions; **-2** coverage matrix shows `n` in each cell and "never run" for missing cells; **-3** live status chip updates within 1 s of `lab.run.progress`; **-4** lab_viewer sees no start buttons. |

### L-02 Attack scenario library  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Browse authorised scenarios with their purpose, variants, expected outcomes and limits. |
| Layout | Category tabs: Forgery · Impersonation · Replay · Channel manipulation · Web (SQLi, XSS, Authentication, Rate limiting, Input validation). Card grid; side panel with full definition. |
| UI components | `ScenarioCard` (id, version, category, short description, "Sandbox only" tag, default limits), `ScenarioDetail` (purpose, preconditions, variants list, expected event/classification/response, pass and fail criteria — sourced from the scenario definition), `VariantTable`. |
| API dependencies | `GET /lab/scenarios`, `GET /lab/scenarios/{id}`. |
| User actions | Search/filter; open details; "Configure & run". |
| Execution states | n/a. |
| Error handling | Empty library: "No scenarios loaded — check the runner deployment"; malformed definition from API shows the card in error state without breaking the grid. |
| Authorization | `lab:runs:read`. |
| Acceptance | **FE-L02-1** all five categories from Attack Lab §3 are present (Forgery, Impersonation, Replay, Channel manipulation, Conventional web with its five sub-scenarios); **-2** each card shows scenario version and definition hash; **-3** "Configure & run" hidden without `lab:runs:execute`. |

### L-03 Scenario configuration  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Configure a scenario safely and reproducibly. |
| Layout | Two-column: form (left) and sticky "Run summary & safety preflight" (right). |
| UI components | Schema-driven `ParamForm` (JSON Schema → Zod → React Hook Form; G-5), `TargetSelect` (only `ACTIVE`, non-expired targets), `SeedInput` (default random, editable, displayed), `LimitsFields` (`max_requests`, `max_rps`, `max_duration_s` with scenario hard caps), `NoiseProfileSelect` and `BackendSelect` (S4, with `ExecutionKindBadge`), `PreflightPanel` (client-side checks: target active/unexpired, limits within caps, calibration VALID for chosen backend via `GET /quantum/calibrations`), `EstimatePanel` (estimated requests/time). |
| API dependencies | `GET /lab/scenarios/{id}`, `GET /lab/targets`, `GET /quantum/backends`, `GET /quantum/calibrations`. |
| User actions | Edit parameters; reset to defaults; save as draft in memory (not persisted) **[V1.1: saved presets]**; proceed to run. |
| Execution states | n/a (pre-run). |
| Error handling | Field errors inline; cross-field errors (e.g., `max_rps × max_duration_s < max_requests`) shown at form level; stale calibration shows warning "verification will be INCONCLUSIVE". |
| Authorization | `lab:runs:execute`. |

**Scenario parameter forms (fields and bounds; server remains authoritative):**
| Scenario | Fields |
|---|---|
| Forgery (S1) | variants multi-select F1–F6; trials per variant (default 100, 1–1000); for F1: tampered settings k ∈ {1,3,6}, shift δ ∈ {0.02,0.05,0.10}; backend; noise profile |
| Impersonation (S2) | variants I-a…I-d; identities (alice/bob/mallory fixed synthetic); trials (default 50); I-d requires "behavioural detection only — not prevention" acknowledgement checkbox |
| Replay (S3) | variants R1–R7; delays (s) list from {1,5,30,90,400}; repetitions (default 25); concurrency N for R7 (≤ 10); includes "flush Redis" (R6) only when the target environment is `local` or `staging-lab` |
| Channel manipulation (S4) | model (`intercept_resend_Z`, `intercept_resend_random`, `over_rotation_Y`, `phase_kick`, `depolarize`, `bellpair_decohere`); fraction f; intensity (ε, λ or v per model); trials per cell (default 200; honest control ≥ 1000 shown as auto-added); circuit family (`direct`/`teleport`); noise profile; backend |
| Web SQLi (S5.1) | corpus (fixed, read-only list shown with hash), delivery (query/body/header), encoded variants toggle, sandbox mode `vulnerable`/`hardened` |
| Web XSS (S5.2) | corpus (fixed), context (reflected/stored), headless-browser check toggle, mode |
| Authentication (S5.3) | A1–A5 selection; attempt caps (≤ 300 / ≤ 500), mode `weak`/`hardened` |
| Rate limiting (S5.4) | L1–L4; rps ≤ 20 (hard cap); duration |
| Input validation (S5.5) | payload classes; platform `/ingest` signed-path check toggle |

Custom payload upload is **not** offered ([Future], requires security review); the corpora are fixed and hashed (S9).

**Acceptance — L-03:** **FE-L03-1** a target that is expired or not `ACTIVE` cannot be selected; **-2** limits above scenario hard caps are rejected client-side and server-side (422 handled); **-3** form values validate identically to server schema for 20 fixture inputs (contract test); **-4** seed is always visible and copied into the run summary; **-5** S4 shows `execution_kind` of the selected backend before submit; **-6** no free-text target URL field exists anywhere in the Lab.

### L-04 Individual attack execution  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Start one run of one scenario. |
| Layout | Route `/runs/new?scenario=<id>` shows configuration (L-03) then a **confirmation dialog**. |
| UI components | `RunConfirmDialog` (scenario/version, target host:port, limits, seed, estimated requests, text "Synthetic data only. This will send attack traffic to the registered sandbox target above."), `SubmitButton` (disabled until checkbox ticked). |
| API dependencies | `POST /lab/runs` with `Idempotency-Key` (UUID generated when dialog opens, reused on retry). |
| User actions | Confirm and start; cancel dialog. |
| Execution states | After 201 → redirect to `/runs/[id]` in `QUEUED`. |
| Error handling | 403 + safety event: show "Safety check failed" with server `detail` (e.g., target not registered/expired) and link to L-11; 422 field errors; 429 (concurrency cap) with countdown; network error retries safely using the same idempotency key. |
| Authorization | `lab:runs:execute` (lab_operator, admin). |
| Acceptance | **FE-L04-1** double-click submits exactly one request (idempotency + button lock); **-2** 403 safety response never navigates away and shows guidance; **-3** the submitted body equals the preview summary (test compares); **-4** confirmation required every time (no "don't ask again"). |

### L-05 Batch attack execution  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Compose and start a batch or experiment (multiple scenarios/configs, optional control arms). |
| Layout | Left: batch builder table (rows = scenario + parameters + repetitions + noise profile). Right: totals (runs, estimated requests, estimated duration), seed hierarchy preview, concurrency (default 1; max per API). |
| UI components | `BatchBuilder` (add/duplicate/remove row, reorder), `RowEditor` (reuses L-03 form in a drawer), `BudgetSummary` (sum of `max_requests`; warns above 10 000), `ArmSelector` (A0/A1/A2 for experiments, per Evaluation §4.4), `ExperimentToggle` (adds benign controls ≥ 1000 trials). |
| API dependencies | `POST /lab/batches`, `POST /lab/experiments`, `POST /lab/batches/{id}/cancel`; status via `GET /lab/runs` (G-3). |
| User actions | Build, validate, confirm (typed phrase "RUN BATCH" for batches estimated > 2 000 requests), start, cancel batch. |
| Execution states | Batch summary shows count by `RunStatus`; overall status derived: any RUNNING → Running; all terminal → Completed/Failed/Cancelled. |
| Error handling | Row-level validation markers; server 422 mapped to rows by `errors[].loc`; partial batch failure keeps completed runs visible. |
| Authorization | `lab:runs:execute`. |
| Acceptance | **FE-L05-1** batch with mixed valid/invalid rows cannot be submitted and highlights invalid rows; **-2** budget warning appears above the stated threshold; **-3** cancel batch moves non-terminal runs to CANCELLED within 5 s (UI reflects via WS); **-4** typed confirmation required above threshold; **-5** experiment mode auto-adds benign control and shows it in the summary. |

### L-06 Live execution monitoring  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Watch a run in real time and cancel it if needed. |
| Layout | Header: scenario, target, seed, config hash, status stepper. Body: progress panel (steps completed/total; requests used/`max_requests`; elapsed/`max_duration_s`; current rps vs `max_rps`) · live step feed · safety panel. |
| UI components | `RunStatusStepper`, `ProgressMeters`, `LiveStepFeed` (last 200 steps), `SafetyPanel` (safety checks passed, violations), `CancelButton`, `KillSwitchLink` (admin). |
| API dependencies | `GET /lab/runs/{id}`, `GET /lab/runs/{id}/steps`, `POST /lab/runs/{id}/cancel`, WS `lab.runs` (`lab.run.progress`, `lab.run.completed`). |
| User actions | Cancel (confirm); copy run id/config hash; open logs/results. |
| Execution states | See §3.0 table; transitions are rendered as they arrive and never regress (a late `RUNNING` message after `COMPLETED` is ignored). |
| Error handling | WS lost → poll `GET /lab/runs/{id}` every 5 s and show banner; FAILED shows failure reason and "sandbox reset queued" notice; cancel on terminal run returns 409 → shown as "Run already finished". |
| Authorization | Read: `lab:runs:read`; cancel: `lab:runs:execute`. |
| Acceptance | **FE-L06-1** progress meters never exceed 100% and match API values; **-2** cancel changes UI to "Cancelling…" immediately and to CANCELLED on confirmation from server; **-3** out-of-order WS messages cannot move status backwards (unit test with shuffled sequences); **-4** WS loss falls back to polling within 5 s; **-5** safety violation event turns header red with message. |

### L-07 Attack event logs  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Inspect what the attack runner did, step by step, and what safety checks ran. |
| Layout | Tabs: Steps · Safety log · Raw JSON. Filter bar (step kind, status code, completed/failed). |
| UI components | `StepTable` (index, kind, request summary, response status, duration, completed), `SafetyLogList`, `JsonViewer` (read-only, text-rendered), `DownloadLogButton` (JSON). |
| API dependencies | `GET /lab/runs/{id}/steps`, `GET /lab/runs/{id}` (safety_log, parameters). |
| User actions | Filter, sort, expand a step, download. |
| Execution states | Live-append while run is active. |
| Error handling | Large runs paginated by cursor; truncated summaries show "truncated (N bytes)". |
| Authorization | `lab:runs:read`. Defender-side events are **not** shown here (lab roles lack `events:read`; ground-truth isolation). |
| Acceptance | **FE-L07-1** steps match API order by `step_index`; **-2** payload contents rendered only via `SafeText` (XSS payload from corpus does not execute); **-3** log download contains no credentials/secrets (fixture check); **-4** safety log entries visible even for COMPLETED runs. |

### L-08 Execution results  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Show detection effectiveness for one run against the scenario's pass criteria. |
| Layout | Summary tiles (TPR, FPR, FAR, precision, median detection latency) each with n and 95% CI · confusion matrix · per-variant table · scenario-specific panel · pass/fail panel · repro block. |
| UI components | `MetricWithCI`, `ConfusionMatrix`, `VariantResultsTable`, `PassCriteriaPanel` (scenario criteria listed with measured values; marked "evaluated in browser from scenario criteria" until the API supplies a verdict), `ChannelPowerPlot` (S4: analytic power vs observed detection with Wilson CIs), `NoiseBudgetNotice` (mandatory for S4), `ReproBlock` (config hash, seed, git SHA, library versions, noise-model hash, `execution_kind`), `GenerateReportButton`. |
| API dependencies | `GET /lab/runs/{id}/evaluation` (shape per API doc §7), `GET /lab/runs/{id}`, `GET /lab/scenarios/{id}`. |
| User actions | Switch variant filter; download JSON; generate report (L-10); re-run with same config. |
| Execution states | If run is not past EVALUATING: "Results not ready" with auto-poll (409 handled as "not ready"). |
| Error handling | Missing CI fields render "CI unavailable" and block report generation. |
| Authorization | `lab:runs:read`. |
| Acceptance | **FE-L08-1** no rate is displayed without n and CI; **-2** S4 results always show `NoiseBudgetNotice` and the `execution_kind`; **-3** zero-failure claims display the rule-of-three upper bound; **-4** 409 "not ready" auto-retries every 3 s up to 2 min; **-5** values equal the API fixture exactly. |

### L-09 Comparative evaluation  **[MVP basic; V1.1 advanced plots]**
| Field | Specification |
|---|---|
| Purpose | Compare experimental arms (A0 classical only vs A1 classical+quantum vs A2 quantum only), backends/noise profiles, or repeated runs. |
| Layout | `/experiments` (session-local list until G-3) · `/experiments/[id]` with comparison table, difference table with CIs, paired-test results, ROC (when available). |
| UI components | `ArmSelector`, `ComparisonTable`, `DifferenceTable` (Δ rate with CI), `McNemarCard` (b, c, statistic, p, exact flag), `StratificationNotice`, `ForestPlot` **[V1.1]**. |
| API dependencies | `POST /lab/experiments`, `GET /lab/experiments/{id}` (G-3), `GET /lab/runs/{id}/evaluation` for each member run. |
| User actions | Select runs/arms, choose metric, export comparison JSON. |
| Execution states | Experiment progress aggregates member runs. |
| Error handling | Mixed `execution_kind` → data shown in separate groups with a notice, never pooled; non-paired designs hide McNemar and state why. |
| Authorization | `lab:runs:read`. |
| Acceptance | **FE-L09-1** paired comparison available only when seeds/traffic match; **-2** differing `execution_kind` always stratified; **-3** comparison table includes n and CI for every cell; **-4** statement shown: "Higher detection in A1 than A0 on classical-attack scenarios is not expected." (guards against misleading claims). |

### L-10 Report generation  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Create reproducible evaluation reports from completed runs/experiments. |
| Layout | Wizard: (1) select runs/experiment · (2) validation checklist · (3) preview · (4) create. List at `/reports`. |
| UI components | `RunPicker`, `ValidationChecklist` (execution kinds stratified, limitations section present, noise-budget statement for S4, n ≥ minimums from Evaluation §4.3 — warnings, not blocks, except missing limitations which blocks), `ReportPreview` (same `ReportViewer` as Defender), `CreateReportButton`. |
| API dependencies | `POST /reports` (with `Idempotency-Key`), `GET /reports`, `GET /reports/{id}`. |
| User actions | Select, validate, create, download JSON/Markdown (G-6). |
| Execution states | Creating → Created; server-side rejection (EVAL-6) shown as checklist failure. |
| Error handling | 422 from validators maps to checklist items. |
| Authorization | `reports:create` (lab_operator, analyst, admin); read for others. |
| Acceptance | **FE-L10-1** report without limitations section cannot be created; **-2** mixed `execution_kind` without stratification is rejected and explained; **-3** created report opens in the viewer with identical content; **-4** idempotent retry does not create duplicates. |

### L-11 Sandbox and target management  **[MVP]**
| Field | Specification |
|---|---|
| Purpose | Register and manage the only hosts the Lab may attack; reset sandboxes; emergency stop. |
| Layout | `/targets`: table + "Register target" drawer + "Safety rules" side panel (S1–S11 summary). `/kill-switch` (admin). |
| UI components | `TargetTable` (name, host:port, resolved IP pins, `network_zone=qs-lab`, status, expiry, last reset), `TargetForm` (name, host, port, expiry ≤ 30 days, mode defaults), `ValidationResultPanel` (shows server validation: private address, not loopback/metadata, DNS pinned), `ResetSandboxButton` (confirm), `DisableTargetButton`, `KillSwitchPanel` (current state, typed confirmation "STOP ALL"). |
| API dependencies | `GET/POST /lab/targets`, `GET/PATCH/DELETE /lab/targets/{id}`, `POST /lab/targets/{id}/reset`, `POST /lab/kill-switch`. |
| User actions | Register, edit expiry, disable, reset, activate/deactivate kill switch. |
| Execution states | Target status chips (`ACTIVE`, `DISABLED`, `EXPIRED`), reset progress (QUEUED→DONE) as reported by API. |
| Error handling | Validation failures (SSRF rules) shown with the specific reason; the UI never offers to override; 409 when deleting a target in use. |
| Authorization | Register/edit/delete: `lab:targets:write` (admin, lab_operator). Reset: `lab:runs:execute`. Kill switch: admin only. |
| Acceptance | **FE-L11-1** attempt to register `127.0.0.1`, `169.254.169.254`, a public IP, or a non-`qs-lab` zone shows the server rejection and does not create a row (Playwright with API); **-2** expired targets are shown as EXPIRED and unusable in L-03; **-3** kill switch requires typed phrase and is admin-only; **-4** target form has no field that accepts a free-form URL outside host/port. |

---

## 4. Design system

Shared by both apps via `packages/ui` and Tailwind tokens (`tailwind.config.ts` in each app extends `packages/ui/tailwind-preset.ts`). Look and feel: dense, calm, neutral — a security operations console. **No decorative animation, gradients, illustrations or marketing visuals.** Motion limited to ≤ 150 ms opacity/transform for drawers and dialogs, disabled under `prefers-reduced-motion`.

### 4.1 Colour tokens
Themes: **dark** (default, SOC-friendly) and **light**, following `prefers-color-scheme`, with a manual toggle stored in `localStorage` key `qs-theme` (a non-sensitive preference).

| Token | Dark | Light | Use |
|---|---|---|---|
| `bg-base` | `#0B1220` | `#F6F8FB` | page background |
| `bg-surface` | `#111A2B` | `#FFFFFF` | cards, tables |
| `bg-elevated` | `#172238` | `#FFFFFF` + shadow | drawers, dialogs, menus |
| `border` | `#263449` | `#D5DCE6` | dividers |
| `text-primary` | `#E6EDF7` | `#0F172A` | body |
| `text-secondary` | `#A9B6C9` | `#475569` | secondary text |
| `text-muted` | `#8A98AE` | `#475569` | captions (light theme uses the secondary colour; `#64748B` is **not** used for text) |
| `accent` | `#3B82F6` (fills) / `#60A5FA` (links, text) | `#1D4ED8` | primary actions, links |
| `sev-critical` | `#EF4444` | `#B91C1C` | severity |
| `sev-high` | `#F97316` | `#C2410C` | severity |
| `sev-medium` | `#EAB308` | `#A16207` | severity |
| `sev-low` | `#38BDF8` | `#0369A1` | severity |
| `sev-info` | `#94A3B8` | `#475569` | severity |
| `ok` | `#22C55E` | `#15803D` | PASS, success |
| `kind-ideal` | `#60A5FA` | `#1D4ED8` | `IDEAL_SIMULATOR` badge |
| `kind-noisy` | `#F59E0B` | `#A16207` | `NOISY_SIMULATOR` badge |
| `kind-hardware` | `#34D399` | `#15803D` | `PHYSICAL_HARDWARE` badge |

**Verdict mapping:** PASS = `ok` + check icon; FAIL = `sev-critical` + x icon; INCONCLUSIVE = `sev-medium` + question icon (distinct from FAIL and PASS).

**Contrast (computed WCAG ratios, text colour on `bg-base` / `bg-surface` / `bg-elevated`, dark theme):** `text-primary` 15.9 / 14.8 / 13.5 · `text-secondary` 9.1 / 8.5 / 7.7 · `text-muted` 6.4 / 6.0 / 5.4 · `#60A5FA` 7.4 / 6.9 / 6.3 · `sev-high` 6.7 / 6.2 / 5.7 · `sev-medium` 9.8 / 9.1 / 8.3 · `sev-low` 8.7 / 8.1 / 7.4 · `sev-info` 7.3 / 6.8 / 6.2 · `ok` 8.2 / 7.6 / 7.0.
**Known limits:** `#3B82F6` on `bg-elevated` is 4.3 and `sev-critical` `#EF4444` on `bg-elevated` is 4.2 (below 4.5) — therefore these two are **used only as fills, borders and large/bold text**, with text labels in `text-primary`; link text uses `#60A5FA`. Light theme: `text-secondary` 7.1/7.6, accent 6.3/6.7, `sev-*` 4.6–6.1 against `bg-base`/`bg-surface` (all ≥ 4.5). A CI test recomputes contrast for every token pair declared in `contrast-pairs.json` and fails below 4.5 (3.0 for large text and UI borders).

### 4.2 Typography
- Families via `next/font` (self-hosted at build, no runtime third-party request): **Inter** (UI) and **JetBrains Mono** (ids, hashes, payloads, counts). Fallbacks: `system-ui, -apple-system, "Segoe UI", sans-serif` / `ui-monospace, SFMono-Regular, Menlo, monospace`.
- Scale (px / line-height): 12/16 caption · 14/20 body & tables (default) · 16/24 large body · 20/28 card title · 24/32 page title · 30/36 KPI numbers.
- Weights 400/500/600. Numerals in tables and KPIs use `font-variant-numeric: tabular-nums`.
- Hashes/ids: mono, truncated middle with full value in `title` and copy button.

### 4.3 Spacing and layout
4 px base unit; scale 4, 8, 12, 16, 24, 32, 48. Card padding 16 (dense) or 24; grid gap 16. Sidebar 240/64 px; header 56 px; content max-width none for tables/streams, 960 px for forms and reports. Border radius 6 px (cards 8). Elevation by border + background step, not heavy shadows.

### 4.4 Components
| Component | Specification |
|---|---|
| **Navigation / Sidebar** | Vertical, grouped, icon + label; active item has 3 px left accent bar + `bg-elevated`; collapsed mode shows tooltips; items hidden if the user lacks the permission; keyboard focusable, `aria-current="page"`. |
| **Header** | App badge, environment tag (prod = red outline, staging = amber, local = grey), `ConnectionIndicator`, notification bell (unread count, last 50 in-memory), user menu. |
| **Cards** | Title row (title, optional help tooltip, actions), body, optional footer with "as of HH:MM:SS". Metric cards show value, delta, `n`. |
| **Tables** | 36 px rows (dense) / 44 px (comfortable toggle), sticky header, sortable columns with `aria-sort`, resizable only for payload columns, row hover + focus ring, selectable rows with checkbox, tabular numerals, virtualised beyond 200 rows (`@tanstack/react-virtual`), column visibility menu, CSV download for visible rows **[V1.1]**. Empty/loading/error per §1.2. |
| **Charts** | Recharts (SVG). Rules: labelled axes with units; direct legends; colour-blind-safe pairing (shape/dash + colour); tooltips keyboard-reachable; every chart has a "View as table" toggle; no 3-D, no pies for more than 5 categories; time axes in UTC with local tooltip; CIs drawn as error bars. |
| **Status indicators** | `StatusDot + label` pairs: severity (5 levels), verdict (3), job status (8), run status (8), connection (3), health (ok/degraded/down). Always icon/shape + text, never colour alone. |
| **Notifications** | *Toasts* (bottom-right, 5 s, max 3) only for user-initiated action results; *Banners* (top of content) for persistent conditions (degraded realtime, stale calibration, kill switch, session expiring); *Inline* for form errors. Errors are never auto-dismissed. `aria-live="polite"` (assertive for kill-switch/safety banners). |
| **Dialogs** | Modal with focus trap, `Esc` to close (except destructive confirmations in progress), initial focus on the least destructive action, typed-phrase confirmation for: revoke credential, kill switch, large batches, target deletion. Drawers for detail views (right side, 480–640 px). |
| **Forms** | React Hook Form + Zod; labels above fields; helper text below; errors replace helper text with icon + text, `aria-describedby` linked; required marked with text "(required)" not asterisk only; submit disabled only during submission; no placeholder-as-label; secrets inputs `autocomplete="off"`/`current-password` as appropriate. |
| **Badges** | `SeverityBadge`, `ClassificationBadge`, `VerdictBadge`, `ExecutionKindBadge` (always includes the words IDEAL / NOISY / HARDWARE), `StatusBadge`. |
| **Code/payload viewer** | `SafeText` + mono font, wrap toggle, 20 KB initial cap, copy button. |

### 4.5 Responsive behaviour
Breakpoints: `sm 640`, `md 768`, `lg 1024`, `xl 1280`, `2xl 1536`. Primary target: **desktop ≥ 1280** (monitoring use). `lg`: sidebar collapsed by default. `md`: tablet — tables lose low-priority columns (column priority metadata), drawers become full-screen. `< md`: **read-only essentials** [MVP]: login, overview tiles, incidents list/detail, event list (no virtual grid), run status; write-heavy screens (resources, batch builder, target registration) show "Use a larger screen" for editing. No horizontal page scroll; wide tables scroll inside their container.

### 4.6 Accessibility (target: WCAG 2.2 AA)
Semantic landmarks (`header`, `nav`, `main`); skip-to-content link; visible 2 px focus ring (`accent`, offset 2 px) on every interactive element; full keyboard operation (tables: arrow-key row navigation optional **[V1.1]**, drawers/dialogs trap focus and restore it); `aria-live` regions for live counters (polite; throttled to ≤ 1 announcement per 10 s); no information conveyed by colour alone; text resizable to 200% without loss; targets ≥ 24×24 px; `prefers-reduced-motion` respected; charts have table alternatives; form errors announced; language attribute set; axe-core checks in CI on every route.

---

## 5. Frontend architecture

### 5.1 Repository layout (per app; same pattern in both)
```text
apps/defender-web/
├── next.config.js              # security headers, no rewrites to API (WS cannot be proxied by Vercel)
├── tailwind.config.ts          # extends packages/ui preset
├── src/
│   ├── middleware.ts           # CSP nonce + headers ONLY (no auth redirects, see 0.2 C1)
│   ├── app/
│   │   ├── layout.tsx          # <html>, fonts, Providers
│   │   ├── (auth)/login/page.tsx, (auth)/login/mfa/page.tsx
│   │   ├── (app)/layout.tsx    # AuthGate + AppShell + ConnectionBanner
│   │   ├── (app)/page.tsx      # D-02
│   │   ├── (app)/events/..., threats/..., incidents/..., responses/..., resources/...
│   │   ├── (app)/quantum/{verification,backends}/...
│   │   ├── (app)/reports/..., health/page.tsx, settings/page.tsx
│   │   ├── error.tsx, not-found.tsx, forbidden.tsx
│   ├── features/<feature>/     # components, hooks, schemas, types, tests per feature
│   ├── components/             # app-local shared (AppShell, Sidebar, Header)
│   ├── lib/
│   │   ├── api/{client.ts,errors.ts,keys.ts,hooks/*.ts}
│   │   ├── auth/{AuthProvider.tsx,AuthGate.tsx,PermissionGate.tsx,usePermission.ts}
│   │   ├── ws/{WsClient.ts,useChannel.ts,reducers.ts}
│   │   ├── forms/{zodFromJsonSchema.ts,mapProblemToForm.ts}
│   │   ├── safe/SafeText.tsx
│   │   ├── env.ts              # validated NEXT_PUBLIC_* (zod)
│   │   └── format/{time.ts,number.ts,hash.ts}
│   └── __tests__/ , e2e specs in /e2e at repo root
packages/ui/        # primitives + tokens + badges + MetricWithCI + SafeText + charts wrappers
packages/api-client # generated types + typed fetch wrapper (shared)
```
`attack-lab-web` mirrors this with `features/{scenarios,runs,batches,targets,experiments,reports}`. **Defender and Lab never import from each other**; shared code lives only in `packages/*`.

### 5.2 TypeScript and code conventions
`strict: true`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`; no `any` (ESLint error), `unknown` + Zod at boundaries; `import type` for types; enums are imported from `@qs/api-client` generated types (never retyped); named exports except Next.js route files; one component per file, `PascalCase.tsx`; hooks `useX.ts`; pure functions in `lib/**` fully unit-tested; no business rules in components; ESLint bans `dangerouslySetInnerHTML`, `innerHTML`, `eval`, `localStorage` for anything except `qs-theme`; Prettier; path aliases `@/*`.

### 5.3 Routing and rendering strategy
Next.js App Router; route groups `(auth)` and `(app)`. **Authenticated data is fetched on the client** (TanStack Query) because the session cookie is host-scoped to the API. Server components render the static shell only. `loading.tsx`/`error.tsx` per segment supply skeleton and boundary behaviour. Filters live in the URL (`useSearchParams`), validated by Zod, so views are shareable and testable.

### 5.4 Authentication state and route protection
- `AuthProvider` holds `{status: 'loading'|'authenticated'|'anonymous', user, permissions, csrfToken, sessionExpiresAt}` **in memory**; initialised by `GET /auth/me` (credentials included). No tokens in storage, cookies written by JS, or URLs.
- `AuthGate` (in `(app)/layout.tsx`): `loading` → full-page skeleton; `anonymous` → `router.replace('/login?next=<relative>')`; `authenticated` → children. 401 from any API call triggers `AuthProvider.invalidate()`.
- `PermissionGate perm=…` and `usePermission()` read `permissions` from `/auth/me`. Route-level guard: pages declare `requiredPermission`; unauthorised users see `ForbiddenPanel` (the API would return 403 anyway).
- Logout clears Query cache, closes WebSocket, calls `POST /auth/logout`, then navigates to `/login`. Cross-tab logout via `BroadcastChannel('qs-auth')`.
- Role/permission change on the server (session rotation) is picked up on the next `GET /auth/me` (every 5 min and on window focus).

### 5.5 API client architecture
`packages/api-client`: generated OpenAPI types + `createClient({baseUrl})` wrapper providing: `credentials: 'include'`; `X-CSRF-Token` from `AuthProvider` for non-GET; `Idempotency-Key` helper for creating jobs/runs/reports/batches; `X-Request-Id` (client-generated UUID) for correlation; JSON-only; timeout via `AbortController` (default 15 s; long-poll 8 s); problem+json parsing into `ApiError {status,title,detail,requestId,errors[]}`; **no automatic retry** of non-idempotent calls (retry only GET and requests carrying an idempotency key). Query keys come from a central factory (`keys.events(filters)`, etc.). Each resource has typed hooks (`useEvents`, `useIncident`, `usePatchIncident` …) in `lib/api/hooks`. Mutations use optimistic updates only where the server rule is simple (notes, assignee) and always roll back on error.

### 5.6 WebSocket integration
`WsClient` (one instance per app):
1. `POST /ws/tickets {channels}` → `{ticket,url}` (CSRF-protected). Open `wss://…?ticket=…`; send `subscribe` with `last_seq` per channel.
2. State machine: `idle → connecting → open → reconnecting → closed`; exposed as `ConnectionIndicator`.
3. On message: validate envelope with Zod; **drop if `seq <= lastSeq[channel]`**; if `seq > lastSeq+1` → REST resume (`GET /events?after_seq=` for `events`; refetch queries for others); apply to query cache via reducers (prepend, update, remove).
4. `ping` → reply `pong` ≤ 5 s. Reconnect with exponential backoff 1 s → 30 s (jitter ±20%), new ticket each time.
5. Close codes: `4401` → `AuthProvider.invalidate()`; `4403` → drop that channel, show notice; `1013` → full refresh then reconnect; others → backoff.
6. In-memory ring buffer ≤ 2000 events per channel; pause/resume support; never persisted.
7. Hook `useChannel(channel, handler)` handles subscription lifecycle; unmount unsubscribes.

### 5.7 State management
Server state: TanStack Query. Realtime state: reducers writing into Query cache (single source of truth per entity). UI state: React state/context; small Zustand stores only for cross-page UI (stream pause state, sidebar, theme). URL for filters. Forms: React Hook Form. **No Redux.**

### 5.8 Form validation
Zod schemas colocated with features; for Lab scenarios derived from server JSON Schema via `zodFromJsonSchema` with a whitelist of supported keywords (type, enum, minimum/maximum, minLength/maxLength, pattern, required, items); unsupported keyword ⇒ build-time error. Server problem+json `errors[].loc` mapped to fields by `mapProblemToForm`. Client validation never weaker than documented API bounds (e.g., θ ∈ [0, π], shots ≤ 200 000).

### 5.9 Error handling
Hierarchy: field → form → panel (`ErrorPanel`) → route `error.tsx` → global `app/error.tsx`. All unexpected client exceptions are captured by the error boundary, show a generic message with a client-generated `errorId`, and (optional **[V1.1]**) are reported to a logging endpoint; no stack traces in UI. Network errors distinguish offline (`navigator.onLine`) from server errors.

### 5.10 Safe rendering (`SafeText`)
The only component allowed to display attacker-controlled strings: renders as a text node (React escaping), applies length caps, normalises control/bidi characters (replaced by visible `�`-style markers `⟦U+202E⟧`), preserves whitespace optionally, and never interprets Markdown/HTML. Unit tests cover HTML, script, SVG, `javascript:` URLs, bidi override, zero-width and extremely long strings.

### 5.11 Environment variables
| Variable | Scope | Example | Notes |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | both apps | `https://api.example.com/api/v1` | HTTPS in staging/prod; validated in `env.ts` |
| `NEXT_PUBLIC_WS_URL` | both apps | `wss://api.example.com/ws/v1/stream` | |
| `NEXT_PUBLIC_APP_ENV` | both apps | `local\|staging\|prod` | drives environment tag only |
| `NEXT_PUBLIC_APP_NAME` | both apps | `Defender` / `Attack Lab` | optional |
No secrets in `NEXT_PUBLIC_*`; app fails to build if `NEXT_PUBLIC_API_URL` is missing or non-HTTPS when `APP_ENV != local`. Test-only variables (`E2E_BASE_URL`, `E2E_USER_*`) exist only in CI.

### 5.12 Security headers and CSP
Set in `middleware.ts` (nonce) and `next.config.js`: CSP per Security doc §7 (`default-src 'self'; script-src 'self' 'nonce-…'; style-src 'self' 'unsafe-inline'; connect-src 'self' <API origin> <WS origin>; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; object-src 'none'; form-action 'self'`), HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`. CSP violation reporting endpoint **[V1.1]**.

### 5.13 Frontend testing (details in `testing/testing-strategy.md` §H)
Vitest + React Testing Library + MSW (handlers generated from the OpenAPI examples), Playwright for end-to-end, axe-core for accessibility, contrast test for tokens, contract tests that parse every JSON example in API doc §3–§7 through the generated Zod/TS types, banned-phrase test for UI strings.

---

## 6. Acceptance criteria

### 6.1 Global criteria (both apps) — **[MVP]**
| ID | Criterion | Measurement |
|---|---|---|
| FE-G-1 | Type safety | `tsc --noEmit` passes with the strict flags in §5.2; zero `any` (ESLint). |
| FE-G-2 | Security headers | Playwright asserts CSP, HSTS, nosniff, frame-ancestors on every route response; zero CSP violations in the console during e2e flows. |
| FE-G-3 | No storage of secrets | After a full login/browse session, `localStorage`, `sessionStorage`, IndexedDB and non-API cookies contain no token, CSRF value or secret (only `qs-theme`). |
| FE-G-4 | Safe rendering | The XSS corpus (≥ 30 payloads) injected via event/step fixtures renders as text; 0 script executions (Playwright `dialog`/`window` probes). |
| FE-G-5 | Accessibility | axe-core: 0 serious/critical violations on every route in default states; keyboard-only completion of login, filter an event, change incident status (Defender) and configure+start a run (Lab). |
| FE-G-6 | Provenance display | Component tests fail if any component rendering quantum data lacks `ExecutionKindBadge`; banned-phrase test passes (`quantum-secure`, `unbreakable`, `quantum encryption`, `secured by quantum`). |
| FE-G-7 | Realtime correctness | Duplicate and out-of-order WS messages produce correct UI state (unit tests with ≥ 20 shuffled/duplicated sequences); exactly-once rendering across a 10 s disconnect (e2e). |
| FE-G-8 | Error handling | For each status in {401,403,404,409,422,429,503} the corresponding UX is exercised by tests; no raw server text/stack trace is ever displayed. |
| FE-G-9 | Permissions | For each role, an e2e/component matrix confirms hidden/disabled controls for ungranted permissions and correct `ForbiddenPanel` on direct URL access. |
| FE-G-10 | Performance budgets (recorded, enforced after first baseline) | First-load JS ≤ 300 KB gzipped per route (from `next build` output); event table sustains 5 000 events/min with no main-thread task > 100 ms in a Playwright trace; INP p75 < 200 ms in local e2e. |
| FE-G-11 | Contract fidelity | All API examples parse through generated types; OpenAPI diff in CI fails on drift between `packages/api-client/openapi.json` and the backend. |
| FE-G-12 | Test coverage | ≥ 80% line coverage for `src/lib/**` and `src/features/**`; ≥ 95% for `lib/ws`, `lib/safe`, `lib/auth`. |
| FE-G-13 | Separation | A dependency-cruiser rule fails CI if either app imports from the other app. |

### 6.2 MVP vs future
| Area | **[MVP]** (v1.0) | **[V1.1]** | **[Future]** |
|---|---|---|---|
| Defender auth | Login, MFA verify, logout, idle warning | MFA enrolment, password change (needs G-2) | SSO/OIDC |
| Dashboard | KPI tiles, charts, live mini-feed | Custom time ranges, saved layouts | Drag-and-drop widgets |
| Events | Live stream, filters, drawer, pause | CSV export, saved filters | Query language |
| Threats | Classification cards, detections, rule explanations | Rule tuning UI (read-only → proposals) | Threat-intel enrichment |
| Incidents | List, detail, status, notes, self-assign | Assign to others, SLA timers | Ticketing integrations |
| Responses | History, manual action, read-only policy | Policy editing, dry-run toggle | Approval workflows |
| Resources | CRUD, enforcement mode, credentials (one-time secret) | Credential expiry reminders | Bulk import |
| Quantum | Verification list/detail, backends, calibration, jobs | Trend analytics per setting | Hardware backend management UI |
| Reports | View, download JSON/MD | Scheduled reports | PDF export |
| System | Health grid, read-only settings | User management | Audit log explorer |
| Lab scenarios | Library, config, single run, batch, live monitor, logs, results, basic comparison, report creation, targets, kill switch | Saved presets, forest plots | Scenario editor, scheduled runs, custom corpora (after review) |
| Platform | Dark/light, desktop-first, read-only essentials on mobile | Table keyboard navigation, CSP report endpoint | i18n, PWA |

### 6.3 Page-level completion rule
A page is **complete** when: (1) all its `FE-*` criteria pass in CI; (2) loading, empty, and error states each have a component test; (3) its permissions matrix is tested for every role; (4) axe reports 0 serious/critical; (5) it uses only endpoints from API doc §3 (or accepted §0.3 addenda); (6) the Task Report in the PR lists any deviation.
