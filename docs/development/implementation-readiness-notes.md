# QuantumShield implementation readiness notes

**Purpose:** Record cross-document decisions to apply before implementation. This file supplements, and does not replace, the individual specifications.

## Documentation import

Import all ten supplied Markdown documents under `docs/` and keep `README.md` at the repository root. The backlog must not require `docs/README.md`; create a docs index only if the team explicitly chooses to add one.

## CSRF decision

`ADR-FE-001-csrf-token-transport.md` is the accepted MVP decision. The synchronizer token is returned by login and `/auth/me`, kept in frontend memory, and sent in `X-CSRF-Token`. Do not implement a JavaScript-readable CSRF cookie or double-submit cookie. Exact Origin validation remains mandatory.

## API contract additions

The API contract's §3.8 defines the frontend-required MVP endpoints and response shapes for metrics overview, lab batch detail, experiment listing, run filters, scenario parameter JSON Schema, report export, and recent quantum verifications. Implement those contracts rather than inventing frontend-only endpoints.

## Solo-maintainer repository settings

Do not configure a mandatory one-approving-review rule if only one maintainer exists. Require pull requests and status checks where practical, protect against force-push/deletion, and use a documented self-review checklist until a second eligible reviewer is available.

## Scientific and security claim boundary

Describe Qiskit Aer results as simulation. Describe QVE as quantum-assisted verification evidence within the defined trusted-worker and classical-authentication model. Do not market it as a physical quantum digital signature, quantum-secure HTTP, or database protection.
