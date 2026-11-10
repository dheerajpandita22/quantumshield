# QuantumShield — Technical Foundation (Day 1)

**Status:** Design specification v1.0. Authored before the repository exists.
**Nothing in these documents has been implemented, executed, or tested.** Code fragments are *normative specification sketches*, not a codebase; Antigravity owns the implementation.

## Document map

| Path | Content |
|---|---|
| `architecture/system-architecture.md` | Components, diagrams, trust boundaries, jobs, realtime, deployment, monorepo |
| `quantum/quantum-protocol-spec.md` | RY/RZ states, Bell pairs, teleportation derivation, measurement, noise, verification statistics, backend abstraction, limitations |
| `security/hybrid-security-architecture.md` | Classical controls, request-signing spec, quantum-vs-classical responsibilities, threat model |
| `security/attack-lab-methodology.md` | Safety rules, sandbox design, Scenarios 1–5 with pass/fail criteria |
| `api/api-contracts-and-schema.md` | Canonical enums, REST/WS contracts with JSON examples, PostgreSQL DDL |
| `evaluation/detection-and-evaluation.md` | Detection pipeline, response policy, evaluation statistics, reproducibility |
| `development/backlog-risks-review.md` | Implementation backlog, acceptance gates, code-review criteria, risk register |

## Known gap in the source assignment
The master assignment text ends mid-sentence in Assignment Four, Scenario 5 ("These conventional…"). Scenarios 1–5 are fully specified here. Material for any later assignments (if they exist) was inferred from the "Claude — Architecture and Research" list in §3 of the assignment. **Please send the remainder so I can reconcile.**

## Global conventions
- **Qiskit bit order:** bitstrings are little-endian (`q_{n-1}…q_0`). Every parser must document and test this.
- **Provenance rule:** every quantum result carries `execution_kind ∈ {IDEAL_SIMULATOR, NOISY_SIMULATOR, PHYSICAL_HARDWARE}`. Aer is never `PHYSICAL_HARDWARE`.
- **Honesty rule:** the quantum layer is an *additive, experimental* verification layer. It never overrides a classical rejection and is never described as securing HTTP, TLS, or PostgreSQL.
- **Time:** UTC, RFC 3339 in APIs, `timestamptz` in PostgreSQL.
- **IDs:** UUIDv7 (time-ordered) as `uuid`.
- Requirement keywords MUST / SHOULD / MAY follow RFC 2119.
