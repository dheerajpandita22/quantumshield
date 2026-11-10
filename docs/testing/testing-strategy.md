# QuantumShield — Testing Strategy

**Status:** Specification v1.0, written before any code exists. **No test described here has been written or run.** Expected values below were derived analytically and cross-checked with a small independent NumPy calculation during authoring; they must still be re-verified against the Qiskit/Aer versions pinned in ADR-001.
**Applies to:** the whole monorepo. Aligned with `architecture/system-architecture.md`, `quantum/quantum-protocol-spec.md`, `security/hybrid-security-architecture.md`, `security/attack-lab-methodology.md`, `api/api-contracts-and-schema.md`, `evaluation/detection-and-evaluation.md`, `frontend/application-specification.md`.
**Relationship to earlier text:** expands Appendix B of `development/antigravity_implementation_backlog.md` (which remains the summary); acceptance IDs (`Q-*`, `SEC-*`, `LAB-*`, `API-*`, `EVAL-*`, `ARC-*`, `FE-*`) are the contract, test IDs below (`T-…`) are how they are verified.

**Scope note.** The brief that requested this document ends at the heading "C. Database tests". Sections A (quantum), B (backend API) and C (database) are specified as requested. Sections D–L (detection, Attack Lab, security, frontend, end-to-end/failure, performance, data/fixtures, CI gates, traceability) are added so the strategy covers the full architecture; please send the rest of the brief if it prescribes different content.

---

## 1. Principles

1. **Every acceptance criterion has at least one automated test**, and every test docstring starts with the criterion ID(s) it verifies (e.g. `"""Q-6, T-Q-05: teleportation ideal fidelity"""`). CI enforces the mapping (§K).
2. **Positive and negative tests are paired.** For each control there is a test proving the *broken* variant is detected (e.g., teleportation without corrections, a flipped MAC byte, a request from another organisation).
3. **Fail-closed behaviour is tested** for every dependency outage.
4. **Statistical tests are seeded and tolerance-based.** No exact equality on sampled values (except deterministic outcomes, §1.3).
5. **Provenance is tested everywhere:** any test that touches quantum results asserts `backend.execution_kind`.
6. **Synthetic data only;** no network access in unit tests; no test may target anything but local/ephemeral stacks or registered sandboxes.
7. **Tests describe behaviour, not implementation:** assert observable results (state, counts, HTTP, DB rows) rather than private call sequences, except in the explicit structural tests listed.

### 1.1 Test taxonomy
| Layer | Marker | Location | Runs |
|---|---|---|---|
| Unit | `unit` | `tests/unit/**`, `apps/**/src/**/__tests__` | every PR |
| Quantum fast | `quantum` | `tests/quantum/**` | every PR (reduced shots/trials) |
| Quantum campaign | `slow` | `tests/quantum/slow/**` | nightly, release |
| Integration (API + DB + Redis + worker) | `integration` | `tests/integration/**` | every PR |
| Database | `integration` + `db` | `tests/integration/db/**` | every PR |
| Security | `security` | `tests/security/**`, Semgrep, gitleaks | every PR / release |
| End-to-end | `e2e` | `tests/e2e/**`, `e2e/**` (Playwright) | path-filtered PR, nightly |
| Failure drills | `e2e` + `drill` | `tests/e2e/failure/**` | nightly, release |
| Performance | `perf` | `tests/perf/**` | nightly (non-blocking) |

### 1.2 Execution tiers for quantum tests
| Tier | Backend | `execution_kind` | Role | In CI |
|---|---|---|---|---|
| **T0 — Ideal** | `qiskit.quantum_info.Statevector` (exact) and `AerSimulator()` without noise | `IDEAL_SIMULATOR` | Correctness of circuits and maths; deterministic where possible | Yes, every PR |
| **T1 — Noisy** | `AerSimulator(noise_model=…)` | `NOISY_SIMULATOR` | Noise algebra, calibration, verification statistics, detection power | Yes (reduced) every PR; full nightly |
| **T2 — Hardware** | Provider device (e.g., via Qiskit Runtime) | `PHYSICAL_HARDWARE` | **Not part of v1.** Only a *contract test with a fake provider* runs in CI; real-device runs are manual, quota-limited, labelled, and never gate a merge (§A.17) | Fake provider only |

Statevector tests validate maths; Aer tests validate sampling and the measurement/classical-control path. A test must state its tier in its ID, e.g. `T-Q-05[T0]`.

### 1.3 Tolerance policy (applies to all quantum tests)
- **Deterministic outcome** (analytic probability exactly 0 or 1 in the ideal tier): the sampled count must equal `N` (or `0`) exactly.
- **Analytic amplitudes/expectations:** absolute error ≤ `1e-12` (statevector).
- **Sampled probability** `p̂ = n/N` vs analytic `p`: `|p̂ − p| ≤ 4·SE`, `SE = sqrt(p(1−p)/N)`.
- **Sampled correlator** `ĉ` (value in [−1,1]) vs `c`: `|ĉ − c| ≤ 4·sqrt((1 − c²)/N)`; when `|c| = 1` exact equality in T0.
- **Chi-squared goodness-of-fit:** valid only if every expected count ≥ 5; failure criterion `p-value < 1e-3`.
- **Flake budget:** one two-sided 4-SE comparison fails by chance with probability `6.3 × 10⁻⁵`; a suite of 500 such comparisons would fail somewhere with probability ≈ 3.1% **if seeds were not fixed**. Therefore every stochastic test uses a **fixed seed recorded in the test**, making it deterministic for a given Qiskit/Aer version. When the pinned library version changes, the suite is re-baselined once; a failure on re-baseline triggers investigation, **not** a seed change, unless the failure is shown to be a pure chance event (rerun with 3 new seeds, all must pass; document in the PR).
- **Default shots:** N = 8192 (state/measurement checks), 4096 per basis (tomography), 16384 (post-selected branch checks), 20000 (noise algebra), 1024 per setting (verification) unless a test states otherwise.

---

## A. Quantum engine tests

Common fixtures: `state_table.json` (θ, φ, analytic `P_Z, P_X, P_Y`, Bloch vector — from Quantum spec §1.3), `seeds.py` (named constants), `noise_profiles.py`, `analytic.py` (the library's own analytic functions are **not** used as the oracle for themselves; the oracle is the NumPy/Statevector calculation in the test).

### T-Q-01 — RY(θ) state preparation  *(Q-1, Q-2, Q-3)*
| Item | Specification |
|---|---|
| Objective | Verify `RY(θ)\|0⟩ = cos(θ/2)\|0⟩ + sin(θ/2)\|1⟩` and measurement probabilities. |
| Setup | One-qubit circuit `ry(θ)`; T0 statevector, then Aer sampling (seeded). |
| Inputs | θ ∈ {0, π/6, π/4, π/3, π/2, 2π/3, π}; N = 8192. |
| Expected | Statevector amplitudes `[cos θ/2, sin θ/2]` (real). `P_Z(0)=cos²(θ/2)`. θ=0 ⇒ all shots `'0'`; θ=π ⇒ all shots `'1'`; θ=π/2 ⇒ ½. Bloch `(sin θ, 0, cos θ)`. |
| Tolerance | Amplitudes ≤ 1e-12; sampled probabilities 4-SE; θ∈{0,π} exact. |
| Failure | Mistaking θ for θ/2 (θ=π/2 giving P=0.25 or 1); sign error (negative sine); non-zero imaginary part; `⟨Y⟩ ≠ 0` beyond 1e-12. |

### T-Q-02 — Phase-sensitive state preparation `RZ(φ)RY(θ)`  *(Q-1, Q-2)*
| Item | Specification |
|---|---|
| Objective | Verify relative-phase encoding and Bloch vector `(sinθ cosφ, sinθ sinφ, cosθ)`; confirm φ is invisible in Z but visible in X/Y; confirm RZ sign convention. |
| Setup | `ry(θ)` then `rz(φ)`; statevector and sampling in X, Y, Z bases. |
| Inputs | Table rows of Quantum §1.3 plus (θ,φ) = (1.0, 0.7), (π/2, π/2), (π/2, π), (π/3, 3π/2); N = 8192. |
| Expected | `P_X(0)=½(1+sinθ cosφ)`, `P_Y(0)=½(1+sinθ sinφ)`, `P_Z(0)=½(1+cosθ)`. (π/2, π/2): `P_Y(0)=1` (this fails if RZ sign or the S†H rotation is wrong). For θ=π/3 the four φ ∈ {0, π/2, π, 3π/2} give identical `P_Z` but different `P_X/P_Y`. State vector equals `e^{−iφ/2}(cos(θ/2)\|0⟩ + e^{iφ}sin(θ/2)\|1⟩)`. |
| Tolerance | 1e-12 (statevector); 4-SE (sampling); deterministic cases exact. |
| Failure | `P_Y(0)=0` at (π/2, π/2) (opposite sign convention); `P_Z` depends on φ; global-phase-sensitive comparison used. |

### T-Q-03 — Bell-pair generation  *(Q-4)*
| Item | Specification |
|---|---|
| Objective | `H(q0)`, `CX(q0→q1)` produces `\|Φ⁺⟩`. |
| Setup | Two-qubit circuit; T0 statevector then Aer counts. Variant B: prepare `q1` in `\|1⟩` first. |
| Inputs | N = 8192. |
| Expected | Statevector `(\|00⟩+\|11⟩)/√2`; fidelity with `\|Φ⁺⟩` = 1 within 1e-12. Counts contain **only** keys `'00'` and `'11'`; `n00 ∈ [N/2 ± 4·√(N/4)] = [4096 ± 181]`. Variant B yields `(\|01⟩+\|10⟩)/√2`: only keys `'01'` and `'10'`. Probability of `01/10` in the main variant is exactly 0. |
| Tolerance | Fidelity ≥ 1 − 1e-12; counts as stated. |
| Failure | Any `'01'/'10'` in ideal main variant; CNOT direction reversed (Variant B distinguishes control from target); unequal weights beyond tolerance. |

### T-Q-04 — Bell-state correlations and entanglement witness  *(Q-4, Q-5)*
| Item | Specification |
|---|---|
| Objective | Verify ZZ, XX, YY correlators and `F_{Φ⁺} = ¼(1 + ⟨XX⟩ − ⟨YY⟩ + ⟨ZZ⟩)`; verify the witness reacts to noise as predicted. |
| Setup | Bell circuit with two-qubit basis rotation (H for X; S†,H for Y) on both qubits; correlator `ĉ = (n_equal − n_different)/N`. T0 and T1. |
| Inputs | T0: N = 8192. T1: explicit bit-flip channel of probability `p = 0.05` on **both** qubits applied after Bell preparation via labelled `id` gates (noise attached only to `id`; `transpile(optimization_level=0)` so the gates are not removed), N = 20000. |
| Expected | T0: `⟨ZZ⟩=+1`, `⟨XX⟩=+1`, `⟨YY⟩=−1`, each **exact** (ZZ,XX: zero "different" outcomes; YY: zero "equal" outcomes); `F=1`. T1: `⟨XX⟩=1`, `⟨ZZ⟩=(1−2p)²=0.81`, `⟨YY⟩=−0.81`, `F=0.905`; lower 99% bound of `F` > 0.5 (entanglement witnessed). White-noise Bell state of visibility `v`: `F=(1+3v)/4` (parametrised check at v = 0.2, 0.5, 0.9 using Aer depolarising of strength λ = 1 − v on **one** qubit only, via a labelled `id`; entangled iff `F>½ ⇔ v>1/3`). |
| Tolerance | T0 exact; T1 correlators within 4·√((1−c²)/N); `F` SE by error propagation. |
| Failure | YY expected sign wrong (+1); `⟨XX⟩` reduced by bit-flip (means noise applied wrongly); **vacuous pass** — a sanity assertion requires that in T1 `⟨ZZ⟩` differs from 1 by > 4 SE (proves noise was actually applied). |

### T-Q-05 — Quantum teleportation (end-to-end)  *(Q-6)*
| Item | Specification |
|---|---|
| Objective | Teleportation reproduces the input state on Bob's qubit with real classical feed-forward. |
| Setup | Circuit of Quantum §3.4 (`c1→X` first, then `c0→Z` on `q2`), Bob measured in basis X/Y/Z (tomography); T0 Aer with dynamic circuits. |
| Inputs | Six axis states {θ,φ} = (0,0), (π,0), (π/2,0), (π/2,π), (π/2,π/2), (π/2,3π/2); generic states (1.0,0.7), (2.2,4.1), (0.4,5.5); N = 4096 per basis. |
| Expected | **Deterministic strong checks:** for `\|1⟩` Bob's Z result is `'1'` in all N shots; for `\|+⟩` Bob's X result `'0'` in all shots; for `\|+i⟩` Bob's Y result `'0'` in all shots (these would be 50/50 without corrections). Tomography fidelity `F̂ = ½(1 + r̂·r_target) ≥ 0.98` for all states. |
| Tolerance | Deterministic checks exact; `F̂ ≥ 0.98` (worst-case σ_F ≈ 0.0064 at N=4096, i.e. ≈3σ margin). |
| Failure | Any deterministic check fails; fidelity ≈ 0.5 (corrections missing/misplaced); exceptions from unsupported dynamic circuit construct (reported to Claude per ADR-001). |

### T-Q-06 — Bell-basis measurement outcomes  *(Q-6)*
| Item | Specification |
|---|---|
| Objective | Alice's outcomes `(c0,c1)` are uniform for every input state, and Bob's pre-correction state in each branch is `X^{m1}Z^{m0}\|ψ⟩`. |
| Setup | Teleportation with `apply_corrections=False` (test-only flag), Bob measured in X, Y, Z; results grouped by `(m0,m1)` using the named-register parser. |
| Inputs | States as T-Q-05 (generic ones are essential); N = 16384 per basis. |
| Expected | (a) Each of the four outcomes has probability ¼; χ² goodness-of-fit df=3, expected count 4096 ≥ 5. (b) Bob's Bloch vector per branch, for input `r=(x,y,z)`: `(0,0)→(x,y,z)`; `(0,1)→(x,−y,−z)`; `(1,0)→(−x,−y,z)`; `(1,1)→(−x,y,−z)` (numerically verified for (θ,φ)=(1.0,0.7)). (c) Marginal over all outcomes: Bob's Bloch vector `→ 0` (no-signalling), `\|r̂\| < 4·SE`. |
| Tolerance | χ² p ≥ 1e-3; branch components within 4·SE with ≈ N/4 shots per branch; marginal `\|r̂_i\| ≤ 4/√N`. |
| Failure | Non-uniform outcomes (broken Bell measurement); wrong branch transform (e.g., classical bits swapped in the parser — Q-14 endianness bug); non-zero marginal (signalling bug). |

### T-Q-07 — Classical feed-forward corrections (mutation tests)  *(Q-8)*
| Item | Specification |
|---|---|
| Objective | Prove the corrections are necessary, correct and correctly wired. |
| Setup | Variants of the teleportation circuit: M0 correct; M1 drop Z only; M2 drop X only; M3 swap control bits (`c0→X`, `c1→Z`); M4 corrections applied in opposite order (Z then X); M5 deferred-measurement coherent variant (`cx(1,2); cz(0,2)`) used only as a cross-check. |
| Inputs | Generic state (θ,φ)=(1.0,0.7) (all Bloch components ≠ 0), plus six axis states; N = 4096 per basis. |
| Expected | Branch-averaged fidelity for `\|ψ⟩` with Bloch vector `(x,y,z)`: **M0** = 1 (`F̂ ≥ 0.98`). **M1** (no Z) averages Bloch to `(0,0,z)` ⇒ `F = ½(1+z²)`. **M2** (no X) ⇒ `(x,0,0)`, `F = ½(1+x²)`. **M3** (swapped controls) ⇒ `(0,y,0)`, `F = ½(1+y²)`. For (θ,φ)=(1.0,0.7): M1 = 0.646, M2 = 0.707, M3 = 0.647 (verified numerically at authoring). **M4 must equal M0** (`ZX = −XZ`: global phase only), `F̂ ≥ 0.98`. M5 reproduces M0's statistics but is flagged by a structural test as *not teleportation*. |
| Tolerance | `\|F̂ − F_oracle\| ≤ 4σ_F` for M1–M3 (oracle computed in the test with NumPy, not by library code); `F̂_M4 ≥ 0.98`. |
| Failure | M1/M2/M3 pass the `≥ 0.98` fidelity check (test would be vacuous); M4 flagged as wrong (misunderstanding of global phase); **structural test:** after the Alice measurements there is no multi-qubit gate acting on `q2` from `q0/q1` in the production circuit — only classically-conditioned single-qubit gates. |

### T-Q-08 — State reconstruction (tomography)  *(Q-6)*
| Item | Specification |
|---|---|
| Objective | The tomography estimator returns correct Bloch vector, fidelity and uncertainty for known states and for known channels. |
| Setup | Estimator tested (a) directly on prepared states, (b) after teleportation across a Bell pair degraded by white noise of visibility `v` (Aer depolarising of strength `λ=1−v` on one Bell half; implemented via a labelled `id`, `optimization_level=0`). |
| Inputs | (a) states of T-Q-02; (b) v ∈ {1, 0.9, 0.8, 0.5, 0.3}; six axis states averaged; N = 4096 per basis. |
| Expected | (a) `\|r̂ − r\| ≤ 4/√N` per component; `F̂ ≥ 0.98`. (b) teleported Bloch vector `v·r`; `F = (1+v)/2` ⇒ 1, 0.95, 0.90, 0.75, 0.65. Six-state average fidelity compared with classical limit **2/3**: exceeds 2/3 iff `v > 1/3`, so v=0.5 passes (0.75 > 0.667) and v=0.3 **must not** be reported as beating the classical limit. |
| Tolerance | `\|F̂ − (1+v)/2\| ≤ 4σ_F` with `σ_F ≤ 0.5·√((2/3)/N) ≈ 0.0064`. |
| Failure | Estimator reports `F>2/3` at v=0.3 (benchmark logic wrong); SE formula under-estimates (empirical std over 200 seeded repeats differs from reported SE by > 20%). |

### T-Q-09 — Global-phase-aware state comparison  *(Q-6)*
| Item | Specification |
|---|---|
| Objective | The comparison utility treats states differing only by a global phase as equal and distinguishes genuinely different states. |
| Setup | Pure statevectors; function `states_equivalent(a,b,tol)` using `\|⟨a\|b⟩\|²`. Mixed case: Bob's reduced density matrix vs pure target using `F=⟨ψ\|ρ\|ψ⟩`. |
| Inputs | `\|ψ⟩` and `e^{iδ}\|ψ⟩` for δ ∈ {0, π/3, π, −1.2}; `Z X\|ψ⟩` vs `X Z\|ψ⟩` (differ by −1); orthogonal pairs (`\|0⟩,\|1⟩`); `\|+⟩` vs `\|−⟩`; near-equal states differing by 1e-3 rotation. |
| Expected | Equal-up-to-phase pairs ⇒ `True` with `\|⟨a\|b⟩\|² ≥ 1 − 1e-12`; orthogonal ⇒ `False`, overlap 0; 1e-3 rotation ⇒ overlap `cos²(5e-4) ≈ 1 − 2.5e-7`, i.e. `False` at tol=1e-12 but `True` at tol=1e-6. A **negative control** asserts that element-wise `np.allclose(a,b)` is `False` for the phase-shifted pairs (documenting why it must not be used). |
| Tolerance | 1e-12 (default), explicit per call. |
| Failure | Phase-shifted equal states reported different; orthogonal states reported equal; tolerance silently loosened. |

### T-Q-10 — X-basis measurement  *(Q-2)*
| Item | Specification |
|---|---|
| Objective | `H` before Z-measurement implements X-basis measurement. |
| Setup | One qubit, prepare, apply `h`, measure. Mutants: no `h`; `sdg` instead of `h`. |
| Inputs | `\|+⟩`(θ=π/2,φ=0), `\|−⟩`(π/2,π), `\|0⟩`, `\|1⟩`, `\|+i⟩`; N = 8192. |
| Expected | `\|+⟩→'0'` always; `\|−⟩→'1'` always; `\|0⟩,\|1⟩,\|+i⟩ → ½`. Mutant "no h" gives `\|+⟩→½` (detected). |
| Tolerance | Deterministic cases exact; others 4-SE. |
| Failure | Deterministic cases not exact; mutants not detected. |

### T-Q-11 — Y-basis measurement  *(Q-2, Q-3)*
| Item | Specification |
|---|---|
| Objective | `S†` then `H` implements Y-basis measurement; RY-only states give `P=½`. |
| Setup | One qubit, prepare, `sdg`, `h`, measure. Mutants: `h` only; `s` then `h`. |
| Inputs | `\|+i⟩`(π/2,π/2), `\|−i⟩`(π/2,3π/2), `\|+⟩`, `\|0⟩`, RY-only θ ∈ {0, π/4, π/2, π}; N = 8192. |
| Expected | `\|+i⟩→'0'` always; `\|−i⟩→'1'` always; others ½ (including every RY-only θ, because `⟨Y⟩=0` for real amplitudes). Mutant "h only": `\|+i⟩→½` (detected). Mutant "s then h": `\|+i⟩→'1'` always (detected). |
| Tolerance | Deterministic exact; others 4-SE. |
| Failure | RY-only state shows `P_Y ≠ ½` beyond 4 SE (implies phase leakage); mutants undetected. |

### T-Q-12 — Z-basis measurement and shot statistics  *(Q-2)*
| Item | Specification |
|---|---|
| Objective | Direct measurement, shot counting, seeding and Wilson interval coverage. |
| Setup | Prepare θ values, measure; repeat with 200 different seeds for coverage. |
| Inputs | θ ∈ {π/6, π/3, π/2, 2π/3}; N ∈ {64, 1024, 8192}. |
| Expected | Counts sum to N; same seed ⇒ identical counts; different seeds ⇒ counts differing but statistically consistent. Empirical coverage of the Wilson 95% interval over 200 seeds ∈ [91%, 99%]. |
| Tolerance | Coverage band above (binomial range for 200 trials at 95%). |
| Failure | Seed ignored (counts differ for same seed); counts not summing to N; coverage outside band (formula wrong). |

### T-Q-13 — Noise models  *(Q-9)*
| Item | Specification |
|---|---|
| Objective | Empirical effect of each channel equals the analytic Bloch-vector action (Quantum §6.1). |
| Setup | Prepare state, apply labelled `id` gate carrying exactly one noise type (`optimization_level=0`), measure in X/Y/Z; N = 20000. Plus gate-attached depolarising on `ry` and readout error. |
| Inputs | Bit-flip `p ∈ {0.02, 0.1}`; phase-flip `p ∈ {0.02, 0.1}`; depolarising `λ ∈ {0.05, 0.2}`; readout `(ε0, ε1) ∈ {(0.05,0), (0,0.1), (0.03,0.03)}`; test states with all components ≠ 0 plus axis states. |
| Expected | Bit-flip: `(r_x,(1−2p)r_y,(1−2p)r_z)`; phase-flip: `((1−2p)r_x,(1−2p)r_y,r_z)`; depolarising: `(1−λ)r`. Readout: `p0' = (1−ε0)p0 + ε1(1−p0)` (`\|0⟩` with ε0=0.05 ⇒ `P(1)=0.05`). Depolarising `λ=0.1` attached to `ry` with θ=0 ⇒ `P_Z(0)=1−λ/2=0.95`. `clean` profile equals the ideal backend (counts identical for the same seed). Noise-model hash is identical across runs/processes and changes when any parameter changes. |
| Tolerance | 4-SE per component. |
| Failure | Contraction on the wrong axis; noise absent (vacuous test); hash unstable or insensitive; noise applied to gates not listed in the model. |

### T-Q-14 — Noise calibration  *(Q-10)*
| Item | Specification |
|---|---|
| Objective | Calibration recovers the honest-channel distribution, flags drift, and manages validity. |
| Setup | PR variant: 24 settings, `K_w=5`, `N_cal=2000`; full variant (`slow`): 216 settings, `N_cal=8192`. Backends `aer-noisy-lab-low/medium`. |
| Inputs | (a) honest windows; (b) windows where bit-flip probability is raised from 0.02 to 0.10 in window 3 only; (c) calibration record aged beyond 24 h (frozen clock); (d) noise-hash mismatch. |
| Expected | (a) pooled `p̄_s` within 4·SE of the analytic noisy expectation for all settings; dispersion test flags ≤ 1% of settings at p<0.01 (≤ 2 of 24). (b) ≥ 90% of drift-sensitive settings (|r along measured axis| ≥ 0.7) get `p<0.01` and `φ_s>1`. (c) status `STALE`; verification returns `INCONCLUSIVE`. (d) record rejected (`REJECTED`), verification refuses to use it. Ideal backend: analytic expectations, no sampling. |
| Tolerance | As stated; seeds fixed. |
| Failure | Drift undetected; honest windows flagged excessively; stale/mismatched calibration used silently. |

### T-Q-15 — Quantum verification  *(Q-11, Q-12)*
| Item | Specification |
|---|---|
| Objective | Verification statistics have the designed error rates and decision logic (Quantum §8–§9). |
| Setup | `m=24`, `N=1024`, `α_tot=1e-3`; PR variant 300 honest trials per profile, 30 trials per tamper cell; `slow` variant 2000 / 200. Seeds split: tuning (`seed mod 5 == 0`) vs test. |
| Inputs | Honest channels `lab-low`, `lab-medium`; tamper library of Quantum §9.6 at intensities of Attack Lab Scenario 4; evidence-integrity variants F1–F6 of Scenario 1; forced preconditions (stale calibration, `E<5` for all settings). |
| Expected | (1) **FRR** (non-PASS on honest): `slow`: ≤ 0.5% with 95% Wilson UB ≤ 1%; PR: ≤ 2% (documented looser bound for small n). (2) p-values under null approximately uniform (KS p>0.01). (3) `intercept_resend_Z`, `intercept_resend_random (f≥0.5)`, `over_rotation_Y(ε≥0.2)`, `phase_kick(ε≥0.2)`: detected (FAIL) ≥ 99% (`slow`). (4) `depolarize` within `κ_min` ⇒ **not** detected — asserted by `test_noise_budget_documented_limitation`. (5) MAC invalid / params mismatch / provenance invalid ⇒ `FORGERY` events **before** any statistics are computed (spy asserts statistics function not called). (6) Decision matrix of Quantum §9.5 holds for all 3×… combinations; property: `final==ACCEPT ⇒ classical==ACCEPT ∧ verdict≠FAIL`. (7) `E<5` cells use the exact test and the verdict records the test used. (8) `INCONCLUSIVE` on stale calibration. (9) Achieved detection rate within Wilson CI of the analytic power prediction. |
| Tolerance | Rates with Wilson 95% CIs; thresholds as above. |
| Failure | FRR above bound; strong tamper below 99%; statistics run before MAC check; χ² applied with `E<5`; thresholds tuned on test seeds (disjointness test fails). |

### T-Q-16 — Invalid circuit parameters  *(Q-13, SEC-6, API-7)*
| Item | Specification |
|---|---|
| Objective | Invalid parameters never reach circuit construction, the queue or the worker. |
| Setup | Table-driven (≥ 30 cases) against (a) engine builder functions, (b) `POST /quantum/jobs`, (c) worker payload re-validation. |
| Inputs | θ ∈ {−0.1, π+0.01, NaN, ±inf, "1.0" (string), true}; φ ∈ {NaN, inf, 2π (boundary: allowed range `[0,2π)` ⇒ invalid), −1e-9}; basis `"W"`, `""`, `"x"` (case); `shots` ∈ {0, −1, 200001, 1.5, "100"}; unknown `backend_id`; `PHYSICAL_HARDWARE` backend requested when unavailable; `job_type` unknown; circuits list empty or > limit; unknown extra fields; payload tampered after enqueue (worker side). |
| Expected | Engine: raises `InvalidCircuitParameter` (no circuit created). API: `422` problem+json with `errors[].loc` and `request_id`; no job row, no queue message. Worker: marks job `DEAD` with permanent error (no retry) and emits event. Boundaries: θ=0 and θ=π **valid**; φ=0 valid; shots=200000 valid, 200001 invalid. |
| Tolerance | Exact. |
| Failure | Any invalid input creates a circuit/job; NaN accepted; 500 instead of 422; retry of a permanent error. |

### A.17 Hardware tier (T2) — rules (not run in v1)
1. **Contract test with a fake provider (CI):** a stub backend returns results flagged `PHYSICAL_HARDWARE` with a `provider_job_id`; assertions: (a) DB and API accept it only with `provider_job_id`; (b) a descriptor with `provider='qiskit-aer'` and `PHYSICAL_HARDWARE` is rejected; (c) reports mixing kinds without stratification are rejected; (d) UI shows the hardware badge. The stub is clearly named `FakeHardwareProvider` and its results never reach production tables.
2. **Real-device smoke tests (manual, quota-limited, outside CI):** Bell witness `F>½`, T-Q-04 deterministic-ish checks reformulated as inequalities, teleportation only if `supports_dynamic_circuits=True`. Tolerances derive from the device's reported calibration (readout and two-qubit errors), **not** from Aer expectations; deterministic-equality checks do not apply. Results are stored with full provenance and are **never** pooled with simulator results.
3. If dynamic circuits are unsupported the teleportation test is **skipped with an explicit "unsupported" result**, never replaced by the deferred-measurement variant.
4. Error mitigation, if used, is labelled and tested separately (raw and mitigated both stored).


---

## B. Backend API tests

**Harness (all `integration` tests):** FastAPI app via `httpx.AsyncClient` against real PostgreSQL and Redis (compose services), Celery worker in eager or real mode as noted; fixtures `org_a`, `org_b`; users `admin_a, analyst_a, viewer_a, auditor_a, lab_operator_a, lab_viewer_a, admin_b`; `login(user, app)` helper returning cookie jar + CSRF token; `machine_client(resource)` helper that signs requests with the Security §5.1 algorithm; frozen/injectable clock; fixture that stops/starts Redis/Postgres for outage tests. Status codes follow API doc §2 (400 malformed, 401 unauthenticated, 403 forbidden/CSRF, 404 not found **or other organisation**, 409 conflict, 413 too large, 422 validation, 429 rate-limited, 503 degraded). Where API doc §3 does not state a success code (e.g. logout, cancel), the test **reads the code from the generated OpenAPI** and fails if the OpenAPI declares none.

Every response in every test additionally passes `assert_problem_json_if_error()` (content type `application/problem+json`, has `request_id`, no stack trace or SQL text) and, if quantum data is present, `assert_has_execution_kind()`.

### B.1 Health
| ID | Request | Expected |
|---|---|---|
| T-API-H1 | `GET /health` (no auth) | 200; body status ok; headers include HSTS, nosniff |
| T-API-H2 | `GET /health/ready`, all dependencies up, as anonymous / as admin | 200; anonymous sees only overall status; admin sees per-dependency list |
| T-API-H3 | `GET /health/ready` with Redis stopped | 503; failing dependency named for admin only; no stack trace |
| T-API-H4 | `GET /health/ready` with Postgres stopped | 503; API process stays alive (liveness `/health` still 200) |

### B.2 Authentication  *(SEC-4, SEC-5, SEC-11)*
| ID | Request | Expected |
|---|---|---|
| T-API-A1 | `POST /auth/login` valid, `app:"defender"` | 200; `Set-Cookie: __Host-qs_def_sid=…; HttpOnly; Secure; SameSite=Lax; Path=/` (Secure/prefix relaxed only when `QS_ENV=local`, asserted); body has `csrf_token`, no password echo; session row stores only token hash |
| T-API-A2 | wrong password vs unknown email (50 attempts each, throttle disabled by test config) | 401 for both; **byte-identical bodies**; latency distributions not distinguishable (Mann–Whitney p > 0.01) |
| T-API-A3 | missing `password`; extra field `role`; wrong type | 422 each (`extra=forbid`) |
| T-API-A4 | 6 failed logins/15 min for one account | 6th → 429 with `Retry-After`; `ratelimit.exceeded` event; a correct login during lockout still 429 |
| T-API-A5 | user with TOTP: login → mfa verify wrong code → right code | login 200 `mfa_required:true` and **no privileged session**; wrong code 401; right code 200 and session issued |
| T-API-A6 | `GET /auth/me` without cookie; with expired session (frozen clock +31 min idle; +8 h absolute) | 401 both |
| T-API-A7 | session rotation: change role in DB, call API | old session invalid after rotation rules; new login required |
| T-API-A8 | Lab cookie presented with Defender `Origin`, and vice versa | 401 or 403 (documented), never 200 |
| T-API-A9 | `POST /auth/logout`, then reuse cookie | success code per OpenAPI; reuse → 401 |

### B.3 Authorization  *(SEC-4, ARC-2)*
| ID | Request | Expected |
|---|---|---|
| T-API-Z1 | **Role × route matrix** generated from `permissions.py` and the app route registry | allowed → 2xx; denied → 403; every route has a declared permission (test fails if a route lacks one) |
| T-API-Z2 | Unauthenticated access to every non-public route | 401 |
| T-API-Z3 | Org A user requests org B object (every `{id}` route, incl. incidents, resources, jobs, runs, reports) | 404 (never 403, never 200) |
| T-API-Z4 | Mutating request without `X-CSRF-Token`; with wrong token; with token of another session; with disallowed `Origin` | 403 each |
| T-API-Z5 | Machine HMAC credentials on a human route; session cookie on `/ingest/requests` | 401 / ingest returns 200 `classical:REJECT` (`signature.invalid`) |
| T-API-Z6 | `viewer_a` `PATCH /incidents/{id}`; `lab_viewer_a` `POST /lab/runs`; `analyst_a` `POST /lab/targets`; `lab_operator_a` `PUT /response-policies/{id}` | 403 each |
| T-API-Z7 | Runner service JWT of run A used to cancel/read run B | 403 or 404 (documented), never 200 |
| T-API-Z8 | `ground_truth` access: any role tries to read labels via any endpoint | no endpoint exposes labels; evaluation responses contain no label keys (schema assertion) |

### B.4 Input validation and error handling  *(SEC-6, API-7)*
| ID | Request | Expected |
|---|---|---|
| T-API-V1 | Body of 1 MiB + 1 byte to any POST | 413 |
| T-API-V2 | `Content-Type: text/plain` on JSON route | 400 (as API doc status list; if the backend prefers 415, update the API doc first) |
| T-API-V3 | Unknown fields, JSON depth 50, huge string (1 MB field), NUL bytes, invalid UTF-8 | 422 (or 413) — never 500 |
| T-API-V4 | SQL/HTML/shell strings in text fields (`'; DROP TABLE …`, `<script>`, `$(id)`) | accepted as data where allowed (201/200) and **stored verbatim**; tables intact; response never reflects them unescaped as HTML; or 422 where field pattern forbids |
| T-API-V5 | Pagination `limit=100000`, `limit=-1`, malformed `cursor` | 422 |
| T-API-V6 | Unknown route; wrong method | 404 / 405 as `problem+json` |
| T-API-V7 | Force an unhandled exception in a test-only route | 500 generic problem+json with `request_id`; no stack trace; error logged with same `request_id`; secret fields absent from the log |
| T-API-V8 | 500 malformed payloads per route generated from OpenAPI (Schemathesis-style) | zero 5xx, zero stack traces, no hangs > 5 s |

### B.5 Quantum jobs, status and results  *(API-2, Q-13, ARC-4)*
| ID | Request | Expected |
|---|---|---|
| T-API-Q1 | `POST /quantum/jobs` valid tomography job (`Idempotency-Key: k1`) | 201; `status:"QUEUED"`; `backend.execution_kind` present; row in `quantum_jobs`; queue message exists |
| T-API-Q2 | Same key and same body again | existing job returned (same `id`), no second row/message |
| T-API-Q3 | Same key, **different** body | 409 *(behaviour proposed here; confirm in API doc addendum)* |
| T-API-Q4 | `shots=200001`; `shots=0`; θ=−0.1; basis `"W"`; unknown `backend_id`; unavailable hardware backend | 422 each (see T-Q-16); no row, no message |
| T-API-Q5 | 201st queued job in org (cap 200) | 429 with `Retry-After` |
| T-API-Q6 | `GET /quantum/jobs/{id}` while QUEUED / RUNNING | 200; correct status; no `results` yet |
| T-API-Q7 | `GET /quantum/jobs/{id}` after SUCCEEDED | 200; `results[]` with `bloch_estimate`, `fidelity ∈ [0,1]`, `fidelity_se > 0`, `classical_bound_average_fidelity ≈ 0.6667`; `backend` complete |
| T-API-Q8 | Unknown uuid; malformed id; other org's job | 404; 422; 404 |
| T-API-Q9 | `POST /quantum/jobs/{id}/cancel` on QUEUED / RUNNING / SUCCEEDED | QUEUED → CANCELLED; RUNNING → CANCEL_REQUESTED then CANCELLED ≤ 5 s; SUCCEEDED → 409 |
| T-API-Q10 | Kill the worker during a RUNNING job | after lease expiry job completes; exactly one result row per circuit (ARC-4) |
| T-API-Q11 | `GET /quantum/backends` | 200; each item has `execution_kind`; no item with `provider='qiskit-aer'` and kind `PHYSICAL_HARDWARE`; hardware absent in v1 |
| T-API-Q12 | `GET /quantum/verifications/{request_id}` after a PASS / FAIL / INCONCLUSIVE ingest | 200; `aggregate`, `structure`, `calibration_id`, `backend`; INCONCLUSIVE contains a reason |
| T-API-Q13 | Calibration `POST /quantum/calibrations` as analyst / viewer | 201 / 403 |

### B.6 Attack scenarios, execution, batches, cancellation  *(LAB-1…5)*
| ID | Request | Expected |
|---|---|---|
| T-API-L1 | `GET /lab/scenarios` as `lab_viewer` / as Defender `viewer` | 200 with all five categories (forgery, impersonation, replay, channel manipulation, web with five sub-scenarios) / 403 |
| T-API-L2 | `GET /lab/scenarios/{id}` known / unknown | 200 with version and definition hash / 404 |
| T-API-L3 | `POST /lab/runs` valid, registered ACTIVE target | 201; `status:"QUEUED"`; `config_hash`, `seed`; labels written (checked via `qs_eval` role only) |
| T-API-L4 | Unregistered target id; expired target; DISABLED target | 403; `lab.safety.violation` event; **no** `attack_runs` row; no packet sent (runner mock asserts no call) |
| T-API-L5 | Limits above scenario caps (`max_rps=1000`); invalid variant name | 422 |
| T-API-L6 | Kill switch ON, then `POST /lab/runs` | refused (status per OpenAPI; 409 recommended) with explanatory `detail`; no row |
| T-API-L7 | Same `Idempotency-Key` twice | one run |
| T-API-L8 | 11th concurrent run in org (cap 10) | 429 |
| T-API-L9 | `POST /lab/batches` with 3 valid rows | 201; 3 runs created with derived seeds `HKDF(batch_seed, i)` |
| T-API-L10 | Batch with 1 invalid row among 3; batch total budget above cap | 422; **zero** runs created (atomic) |
| T-API-L11 | `POST /lab/runs/{id}/cancel` on QUEUED / RUNNING / COMPLETED | CANCELLED / CANCEL → CANCELLED ≤ 5 s and sandbox reset queued / 409 |
| T-API-L12 | `POST /lab/batches/{id}/cancel` | all non-terminal member runs reach CANCELLED ≤ 5 s |
| T-API-L13 | `GET /lab/runs/{id}/steps` pagination | ordered by `step_index`, cursor stable under concurrent appends |
| T-API-L14 | Cancel by `lab_viewer`; kill switch by non-admin | 403 |

### B.7 Security events, incidents, responses  *(SEC-2, EVAL-1…3)*
| ID | Request | Expected |
|---|---|---|
| T-API-E1 | Signed `POST /ingest/requests` valid | 202 `ACCEPT_PROVISIONAL`; `request_id`, `quantum_job_id`; `ingest_requests` row |
| T-API-E2 | Identical request replayed within 60 s | 200 `classical:REJECT`, reason `replay.detected`; event persisted (type, severity MEDIUM, `key_id`); WS `security_event.created` delivered; classification REPLAY |
| T-API-E3 | Timestamp 61 s old; 61 s in the future | 200 REJECT `request.stale` |
| T-API-E4 | One-byte change in body/path/query/timestamp/nonce | 200 REJECT `signature.invalid` |
| T-API-E5 | Unknown / revoked `key_id` | 200 REJECT `identity.unknown_key` |
| T-API-E6 | 50 parallel identical requests | exactly one passes nonce claim; 49 `replay.detected` |
| T-API-E7 | Redis flushed, then replay of pre-flush request | REJECT (fail-closed rule) |
| T-API-E8 | Valid signature, invalid body schema | 422 (validation after authentication of the machine) |
| T-API-E9 | `GET /events` filters (`type,severity,classification,resource_id,from,to,after_seq`) | correct subsets; cursor pagination; cross-org isolation; `limit` bounds |
| T-API-I1 | 3 related events within 15 min | one incident, `event_count=3`, severity per Evaluation §1 |
| T-API-I2 | Events at 14:59 and 15:01 minutes apart (same key) | second creates a new incident (boundary test, frozen clock) |
| T-API-I3 | `PATCH /incidents/{id}` OPEN→INVESTIGATING→CONTAINED→RESOLVED (note supplied) | 200 each |
| T-API-I4 | RESOLVED without note; RESOLVED→OPEN without note | 422; 409 |
| T-API-I5 | `POST /incidents/{id}/notes` | 201; stored verbatim; rendered escaped by the UI (T-FE) |
| T-API-R1 | After replay event, `GET /responses` | AUTO `BLOCK_REQUEST` row with `detection_id`, `expires_at` null for single-request block |
| T-API-R2 | `POST /responses` manual, valid (analyst) | 201; audit row written; WS `response.executed` |
| T-API-R3 | Missing/short reason; unknown action; target of admin session | 422; 422; 409 (safeguard) |
| T-API-R4 | `viewer` manual action | 403 |
| T-API-R5 | > 100 auto actions/min | extra actions suppressed, `system.degraded`-style event, no self-DoS |
| T-API-R6 | Policy `dry_run=true` | actions recorded as *would-have* with no effect on decisions |

### B.8 Evaluation endpoints and reports  *(EVAL-4…7, LAB-6)*
| ID | Request | Expected |
|---|---|---|
| T-API-EV1 | `GET /lab/runs/{id}/evaluation` before EVALUATING completes | 409 "not ready" |
| T-API-EV2 | After COMPLETED | 200; `tp,fn,fp,tn`, `tpr`, `tpr_ci95`, `fpr`, `fpr_ci95`, `median_detection_latency_ms`, `backend`, `noise_budget_statement` (S4); CIs equal an independent `scipy`/`statsmodels` Wilson calculation to 1e-9 |
| T-API-EV3 | Other org's run | 404 |
| T-API-EV4 | `POST /reports` valid | 201; `config_hash`, `environment`, `execution_kinds` filled |
| T-API-EV5 | Report mixing `execution_kind` unstratified; report lacking limitations; report with a rate lacking `n` | 422 each (EVAL-6) |
| T-API-EV6 | `POST /lab/experiments` arms A0/A1/A2 | 201; arms recorded; control group auto-added |
| T-API-EV7 | Evaluation DB role boundary: detection pipeline process queries labels | permission error (also T-DB) |

### B.9 Illustrative test examples (not executed; Antigravity writes the real ones)
```python
async def test_replay_is_rejected(machine_client, db):
    """SEC-2, T-API-E2"""
    req = machine_client.sign("POST", "/api/v1/ingest/requests", body={"resource_id": RES, "action": "transfer"})
    r1 = await machine_client.send(req)
    r2 = await machine_client.send(req)             # identical bytes, same nonce
    assert r1.status_code == 202
    assert r2.status_code == 200
    assert r2.json()["classical"] == "REJECT" and r2.json()["reason"] == "replay.detected"
    ev = await db.fetch_event(event_id=r2.json()["event_id"])
    assert ev.event_type == "replay.detected" and ev.severity in ("MEDIUM", "HIGH")

async def test_cross_org_is_404(login, org_b_incident_id):
    """SEC-4, T-API-Z3"""
    c = await login("analyst_a")
    r = await c.get(f"/api/v1/incidents/{org_b_incident_id}")
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/problem+json")

@pytest.mark.parametrize("payload", INVALID_JOB_PAYLOADS)   # ≥ 30 cases from T-Q-16
async def test_invalid_job_rejected(login, payload, queue, db):
    """Q-13, T-API-Q4"""
    c = await login("analyst_a")
    r = await c.post("/api/v1/quantum/jobs", json=payload, headers={"Idempotency-Key": str(uuid4())})
    assert r.status_code == 422 and r.json()["request_id"]
    assert await queue.depth() == 0 and await db.count("quantum_jobs") == 0
```

---

## C. Database tests

**Harness:** real PostgreSQL 16 (compose/CI service), each test module gets a fresh database created from migrations (template DB for speed); connections open as each application role (`qs_api`, `qs_worker`, `qs_detect`, `qs_eval`, `qs_migrator`) and as a test-only superuser for tamper simulations. Tests live in `tests/integration/db/`.

| ID | Area | Test | Expected |
|---|---|---|---|
| T-DB-01 | Migrations | `alembic upgrade head` on empty DB; `downgrade base`; `upgrade head` again | all succeed; second upgrade yields schema identical to first (compare `pg_dump --schema-only` normalised) |
| T-DB-02 | Drift | `alembic check`/autogenerate diff after upgrade | empty diff (models == migrations) |
| T-DB-03 | Enum parity | DB enum labels vs Python `StrEnum` vs `enums_expected.json` (API doc §1) | identical sets and order-insensitive equality |
| T-DB-04 | Provenance constraints | insert backend `provider='qiskit-aer'` with kind `PHYSICAL_HARDWARE`; `NOISY_SIMULATOR` without `noise_model_hash`; job `PHYSICAL_HARDWARE` without `provider_job_id` | each raises check violation; the valid counterparts succeed (API-5, Q-13) |
| T-DB-05 | Domain constraints | `shots` 0 and 200001; `port` 0 and 65536; `network_zone` ≠ `'qs-lab'`; `confidence` −0.1 and 1.1; invalid `status` values; `enforcement_mode` invalid | violations raised; boundary values (shots=1, 200000, port=1, 65535, confidence 0 and 1) accepted |
| T-DB-06 | Uniqueness | `(org_id,email)`; `(org_id,idempotency_key)`; `(org_id,evidence_digest)`; `request_nonces (key_id,nonce)`; `token_hash`; `(job_id,circuit_index)` | duplicates rejected; `ON CONFLICT DO NOTHING` paths verified to leave a single row |
| T-DB-07 | Referential integrity | delete parent with children (resource with credentials/events; incident with notes); orphan inserts | FK violations or documented cascades; no orphans possible |
| T-DB-08 | RLS isolation | for **every tenant table**: org A session sees only A rows; session without `app.org_id` sees **0 rows**; INSERT with `org_id` of B fails (`WITH CHECK`/policy); UPDATE moving a row to org B fails | all pass; list of tenant tables is derived from `information_schema` (columns named `org_id`) so new tables cannot escape the test; superuser/owner bypass documented and `FORCE ROW LEVEL SECURITY` verified for app roles (SEC-4) |
| T-DB-09 | Role grants | matrix of roles × tables × {SELECT, INSERT, UPDATE, DELETE, TRUNCATE} against expected grants | `qs_detect`: **no** access to `ground_truth_labels` (SQLSTATE 42501); `qs_api`: INSERT-only on it; `qs_eval`: SELECT; `qs_worker`: no access to `users`, `sessions`; no app role has DDL, `CREATEROLE`, superuser or `COPY PROGRAM` (ARC-3, EVAL-7) |
| T-DB-10 | Ground-truth isolation (schema) | introspect detection-side tables (`security_events`, `detections`, `response_actions`, `incidents`, `ingest_requests`) | no column named `attack_run_id`, `is_attack`, `true_class`, `variant` and no FK to `lab.*` |
| T-DB-11 | Audit append-only | as each app role attempt `UPDATE`, `DELETE`, `TRUNCATE` on `audit_log` | all denied; insert only via `append_audit(...)` |
| T-DB-12 | Audit hash chain | append 100 rows; verifier passes; tamper one row as superuser; verifier fails and names the first bad id; 50 parallel appends for one org | chain valid (advisory lock/serialisation per org); tamper detected (SEC-9); function is `SECURITY DEFINER` with fixed `search_path` (introspection) |
| T-DB-13 | Nonce table | 50 concurrent inserts of same `(key_id,nonce)`; insert into date without partition; partition pre-creation job; retention job drops partitions older than 7 days | exactly 1 success; out-of-range insert handled (default partition or pre-created, never silent loss); retention leaves newer data (SEC-3) |
| T-DB-14 | Job claim/lease | two workers race to claim one job; lease expiry sets job re-claimable; janitor query on 100 000 seeded rows | exactly one claim wins; expired lease reclaimable; `EXPLAIN` shows index scan on `(status, lease_until)` (no seq scan), p95 < 50 ms (ARC-4) |
| T-DB-15 | Result idempotency | insert same `(job_id,circuit_index)` twice with `ON CONFLICT DO NOTHING` | one row; first write wins |
| T-DB-16 | Secrets at rest | introspect columns named like `%secret%`, `%password%`, `%token%`, `%key%` | each is `bytea` suffixed `_enc`/`_hash` (or documented exception); no plaintext candidates; inserted credential round-trips only as ciphertext (SEC-10) |
| T-DB-17 | Timestamps | all `timestamptz`; server timezone UTC; round-trip of tz-aware values | no naive timestamps |
| T-DB-18 | Transactionality | ingest: force failure after `ingest_requests` insert but before job insert | whole transaction rolled back; no orphan request |
| T-DB-19 | Statement timeout | `SELECT pg_sleep(6)` as `qs_api` | cancelled by `statement_timeout=5s` |
| T-DB-20 | Incident dedup | concurrent inserts for the same `dedup_key` (20 threads) | one open incident; counts consistent |
| T-DB-21 | Retention/purge | seed expired sessions/events; run purge jobs | rows beyond retention removed; others intact |
| T-DB-22 | Seed safety | `seed_dev` with `QS_ENV=prod` | refuses; with `local` creates only synthetic rows (names prefixed `SYN-`/`example.test`) |
| T-DB-23 | Performance (nightly) | `GET /events` query plan with 1 M rows (`org_id, created_at DESC` index); `events` filtered by type | index used; p95 < 100 ms |
| T-DB-24 | Backup/restore drill (staging, release) | restore PITR copy; run audit-chain verifier and row counts | chain valid; counts match snapshot |

---

## D. Detection, response and incident tests  *(EVAL-1…3, EVAL-8)*
| ID | Test | Expected |
|---|---|---|
| T-DET-01 | Per-rule corpora: each rule (R-SIG-1 … R-BEH-1) has ≥ 10 positive and ≥ 10 benign look-alike cases in `tests/fixtures/detection/*.jsonl` | all positives hit with documented confidence; **zero** benign hits; benign set includes `O'Brien`, `5 < 6 and 7 > 3`, URLs containing `--`, prose with "select" and "union", HTML-looking user text in free-text fields |
| T-DET-02 | Normalisation | URL-double-encoded, mixed case, Unicode-NFKC, comment-split payloads (`UN/**/ION SEL/**/ECT`) | detected after D0; originals preserved in evidence; > 2 decode passes not performed (no decoding bombs: 1 MB nested-encoding input handled < 100 ms) |
| T-DET-03 | Detection rates on fixed corpora (tuning half used for weights; **test half** for reporting) | SQLi ≥ 95% plain, ≥ 80% encoded; XSS ≥ 95% / ≥ 80%; benign FPR ≤ 1% on ≥ 500 benign queries |
| T-DET-04 | Precedence | ≥ 15 constructed multi-signal cases (e.g., replay + SQLi payload; QVE forgery + rate abuse) | primary classification follows `FORGERY > REPLAY > IMPERSONATION > CHANNEL_MANIPULATION > WEB_SQLI > …`; all contributing rule ids stored (EVAL-2) |
| T-DET-05 | Severity | table-driven base × confidence × criticality × repetition | documented severity, clamped to LOW…CRITICAL |
| T-DET-06 | Behavioural (D4) | synthetic baselines: normal traffic then (a) 10× rate burst, (b) new resource set, (c) new fingerprint | score ≥ 4 for (a),(b),(c) combined; no alert on diurnal variation within baseline; confidence never > 0.8; never auto-block (EVAL-3) |
| T-DET-07 | Quantum mapping (D3) | verdicts PASS/FAIL/INCONCLUSIVE with structure classes | FAIL(structure ≠ NOISE_DRIFT) → CHANNEL_MANIPULATION; MAC/params/provenance → FORGERY; INCONCLUSIVE → UNKNOWN or NOISE_DRIFT; **a classical REJECT is never converted to accept** |
| T-DET-08 | Import boundary | import-linter contract: `backend.detection` must not import `backend.evaluation` or read `ground_truth_labels` | contract passes; deliberately adding the import fails CI (EVAL-7) |
| T-DET-09 | Response policy matrix | one case per row of Evaluation §2 (plus escalation rules) from `policy.default.yaml` | documented action(s), `expires_at` set for throttle/quarantine; reversible (EVAL-3) |
| T-DET-10 | Safeguards | auto-block of an `admin` session; 101st automatic action in a minute; dry-run mode | blocked by safeguard; suppressed + event; recorded-not-executed |
| T-DET-11 | Incident correlation | boundary and concurrency tests (see T-API-I1/I2, T-DB-20) | as stated |
| T-DET-12 | Determinism | same event sequence twice | identical detections, severities, incidents |

---

## E. Attack Lab tests  *(LAB-1…7, Attack Lab §1–§3)*
| ID | Test | Procedure / input | Expected |
|---|---|---|---|
| T-LAB-01 | Target validators | ≥ 30 hostile hosts: `127.0.0.1`, `localhost`, `0.0.0.0`, `169.254.169.254`, `10.0.0.1` outside `qs-lab`, public IPs, IPv6 loopback/link-local, decimal/octal/hex IP encodings, `user@host` tricks, DNS name resolving private-then-public (rebinding), trailing dots, uppercase, unicode homoglyphs | all rejected with a specific reason; valid `qs-lab` targets accepted (LAB-1) |
| T-LAB-02 | Registry signature | tamper any field (`host`, `ip_pins`, `expires_at`) | runner aborts, `lab.safety.violation`, no traffic |
| T-LAB-03 | Guard wrapper | scenario code attempts request to non-pinned IP; exceeds `max_requests`, `max_rps`, `max_duration_s` | blocked/stopped at limits; violation logged; Semgrep rule prevents direct `httpx` in scenarios (static test) |
| T-LAB-04 | Network egress (runs **inside** runner container) | connect to public IP, to API host loopback, to unregistered private port, to metadata address | all fail; `lab.safety.violation` logged (ARC-7, LAB-2) |
| T-LAB-05 | Kill switch | start batch, activate switch | all runs stop ≤ 5 s; new runs refused; state visible in UI/API (LAB-3) |
| T-LAB-06 | Determinism | same scenario config + seed twice | identical attack inputs byte-for-byte (hash of request stream equal); quantum counts identical on same library versions (LAB-4, Q-15) |
| T-LAB-07 | Ground truth written first | crash runner after trial label insert but before send; and vice versa | no unlabeled attack traffic can exist; trial replay is idempotent by `(run_id, step_index)` |
| T-LAB-08 | Ground-truth isolation | detection role cannot read labels; evaluation can; UI/API never expose labels (LAB-6) | as T-DB-09/T-API-Z8 |
| T-LAB-09 | Sandbox reset | run vulnerable scenarios, reset | DB state hash equals seed hash; reset also on FAILED/CANCELLED |
| T-LAB-10 | Vulnerable-mode guard | start sandbox with `mode=vulnerable` and `QS_ENV=prod`, or bound to non-lab interface | process refuses to start |
| T-LAB-11 | Synthetic-only data | scan fixtures/corpora for real-looking emails/phones/domains | CI check passes; denylist test with a seeded bad fixture fails |
| T-LAB-12 | Scenario 1 (forgery) | variants F1–F6, ≥ 100 trials/variant (≥ 25 in PR CI) | 0 forged requests accepted; event/classification/response chain as in Attack Lab §3; benign FRR ≤ 0.5% (95% UB ≤ 1%) |
| T-LAB-13 | Scenario 2 (impersonation) | variants I-a…I-d | I-a/I-b/I-c: 100% rejected or stepped-up; I-d: detection ≥ 80% at ≤ 2% benign FPR, documented as *behavioural detection, not prevention* |
| T-LAB-14 | Scenario 3 (replay) | variants R1–R7 incl. 10 parallel identical requests (R7) and Redis flush (R6) | 0 replays accepted; R7: exactly one passes the nonce claim (or 0 if the original was already processed); R6 fails closed |
| T-LAB-15 | Scenario 4 (channel manipulation) | full sweep of Attack Lab §3 S4 (models × intensities × noise profiles), ≥ 200 trials/cell (`slow`), honest control ≥ 1000 | strong manipulation classes detected ≥ 99% with Wilson CIs; honest FRR bound met; `NoiseBudgetNotice` and `execution_kind` in every report (LAB-7) |
| T-LAB-16 | Scenario 5.1–5.5 | SQLi, XSS, authentication, rate-limiting and input-validation corpora against sandbox `vulnerable` and `hardened` modes | detection thresholds of Attack Lab §3; hardened mode returns no data for any corpus payload; 0 XSS executions in hardened sandbox and in the Defender UI; auth: median detection ≤ 10 attempts; rate-limit bypass = 0; invalid input: 100% 4xx, no stack traces |
| T-LAB-17 | Cancellation and crash recovery | cancel mid-batch; kill runner process | CANCELLED/FAILED with reset queued; no zombie runs after janitor |

---

## F. Security tests  *(SEC-1…12, T1–T24 of the threat model)*
| ID | Test | Expected |
|---|---|---|
| T-SEC-01 | Signing vectors (API doc §8) in Python **and** TypeScript; ± 1-byte mutations of every input; skew boundary 59.9/60.1 s | vector verifies; all mutations fail; boundary behaviour exact (SEC-1) |
| T-SEC-02 | Replay suite (T-API-E2…E7) | all rejected (SEC-2, SEC-3) |
| T-SEC-03 | Authz and tenancy suite (T-API-Z*, T-DB-08/09) | pass (SEC-4) |
| T-SEC-04 | CSRF suite on every mutating route; WebSocket cross-origin handshake; ticket reuse; expired ticket | 403 / handshake rejected (SEC-5, T20) |
| T-SEC-05 | Platform injection resistance: send the SQLi and XSS corpora to **the platform's own** API fields (not the sandbox) | never 5xx, never data leakage, DB intact (row counts, schema hash), responses never reflect HTML unescaped; Semgrep forbids concatenated SQL (SEC-7) |
| T-SEC-06 | Stored XSS path: events/notes with payloads rendered in Defender UI | no script execution (Playwright), CSP present with nonces (SEC-8) |
| T-SEC-07 | Fuzzing: 500 malformed payloads per route from OpenAPI | zero 5xx/stack traces (SEC-6) |
| T-SEC-08 | Secrets: gitleaks (repo + history), log-redaction test (secrets, cookies, signatures never in captured logs), `prod` startup with dev KEK fails | clean / pass (SEC-10) |
| T-SEC-09 | Rate limits: login, ingest, job submission, lab runs, WS tickets | 429 + `Retry-After`; limiter backend failure → fail closed for auth/ingest (SEC-11) |
| T-SEC-10 | SSRF/target registration (T-LAB-01) and DNS re-resolution at run time | rejected (T22) |
| T-SEC-11 | Audit chain tamper (T-DB-12) | detected (SEC-9) |
| T-SEC-12 | Header and cookie checks: HSTS, nosniff, referrer-policy, frame-ancestors, `__Host-` cookie attributes, CORS exact-origin (no wildcard with credentials) | pass |
| T-SEC-13 | Dependency audit: `pip-audit`, `pnpm audit`, SBOM, Trivy on images | no unaccepted HIGH/CRITICAL (Phase 8) |
| T-SEC-14 | ZAP baseline (authenticated) **against the platform's own staging only** | no unaccepted MEDIUM+ findings; never run against third parties or the Lab sandbox as a substitute for scenarios |
| T-SEC-15 | Banned-claims test: UI strings and docs contain none of `quantum-secure`, `unbreakable`, `quantum encryption`, `secured by quantum`; honesty statements present (SEC-12, FE-G-6) | pass |

---

## G. Frontend tests  *(FE-G-1…13, page criteria `FE-D*`, `FE-L*`)*
| ID | Layer | Content |
|---|---|---|
| T-FE-01 | Unit (Vitest) | `lib/ws` reducers (≥ 20 shuffled/duplicated sequences, gaps, resume), `SafeText` (HTML/script/SVG/`javascript:`/bidi/zero-width/very long), `lib/auth` state machine, `mapProblemToForm`, `zodFromJsonSchema` (supported/unsupported keywords), `env.ts` validation |
| T-FE-02 | Component (RTL + MSW) | every page: loading, empty, error (401/403/404/409/422/429/503), permission variants per role; handlers generated from OpenAPI examples; fixtures from API doc §3–§7 |
| T-FE-03 | Contract | every JSON example in the API doc parses through generated types; OpenAPI drift check (FE-G-11) |
| T-FE-04 | Provenance | component test enumerates components that import quantum types and asserts `ExecutionKindBadge` is rendered (FE-G-6) |
| T-FE-05 | Enum coverage | iterate generated enums (`Classification`, `JobStatus`, `RunStatus`, `Severity`, `Verdict`, `ResponseAction`) and assert label+colour+icon exist (FE-D06-1, FE-D09-1) |
| T-FE-06 | Accessibility | axe on every route and key states; contrast test over `contrast-pairs.json` ≥ 4.5 (text) / 3.0 (UI) |
| T-FE-07 | E2E (Playwright, real local stack) | Defender: login → overview → events live (WS) → open event → incident status change → manual response → quantum verification detail → report view. Lab: login → register target → configure S3 → run → live monitor → cancel → results → report. Storage scan (FE-G-3), CSP/console cleanliness (FE-G-2), XSS corpus (FE-G-4) |
| T-FE-08 | Realtime e2e | cut network 10 s (Playwright `context.setOffline`) → exactly-once rendering (FE-G-7); WS close codes 4401/4403/1013 behaviours |
| T-FE-09 | Permissions | role matrix e2e: each role × representative routes/buttons (FE-G-9) |
| T-FE-10 | Performance | event table with 5 000 events/min fixture; long-task budget; bundle size from `next build` (FE-G-10) |
| T-FE-11 | Architecture | dependency-cruiser: no cross-import between `apps/defender-web` and `apps/attack-lab-web` (FE-G-13) |

---

## H. End-to-end and failure-drill tests  *(ARC-4…7)*
| ID | Test | Expected |
|---|---|---|
| T-E2E-01 | **Vertical slice:** `alice` signed request → classical checks → quantum job on `aer-noisy-lab-low` → verdict → event → WebSocket → Defender stream | PASS shown with `NOISY_SIMULATOR` badge; latency recorded |
| T-E2E-02 | Scenarios 1–5 through the Lab API/UI (PR sizes; full sizes nightly) | all Attack Lab §3 pass criteria; Defender UI displays detections; evaluation report generated |
| T-E2E-03 | Reproducibility: same experiment config + seeds twice | identical trial tables (hash) and counts (EVAL-5, LAB-4, Q-15) |
| T-E2E-04 | Drill: kill worker mid-job | job completes after lease; no duplicates (ARC-4) |
| T-E2E-05 | Drill: stop Redis | ingest on BLOCKING resources rejects; `system.degraded` event; recovery after restart; no acceptance during outage (ARC-5) |
| T-E2E-06 | Drill: stop PostgreSQL | 503; no writes accepted; recovery; no partial data |
| T-E2E-07 | Drill: network cut to WebSocket | exactly-once UI state after reconnect (ARC-6) |
| T-E2E-08 | Drill: runner crash | run FAILED, sandbox reset, janitor clears |
| T-E2E-09 | Drill: stale calibration | verdict INCONCLUSIVE; BLOCKING rejects; calibration job auto-queued; banner shown |
| T-E2E-10 | Drill: kill switch during batch | stop ≤ 5 s (LAB-3) |

---

## I. Performance and load tests (non-blocking; recorded)  *(P7-07)*
| ID | Measurement | Sanity budget (local reference machine; record specs) |
|---|---|---|
| T-PERF-01 | Ingest classical phase | p95 < 100 ms at 50 rps |
| T-PERF-02 | Verification latency (m=24, N=1024, noisy sim) | p95 recorded; budget set after first baseline |
| T-PERF-03 | Worker throughput (jobs/min) vs worker count 1,2,4 | roughly linear scaling to core count |
| T-PERF-04 | WebSocket fan-out latency, 100 clients | p95 < 250 ms |
| T-PERF-05 | Rate limiter overhead | < 2 ms p95 |
| T-PERF-06 | Soak 1 h at 20 rps | no memory growth > 20%, no errors, queues drain |
Budgets become blocking only after a baseline is accepted by the project owner.

---

## J. Test data, fixtures and environments
1. **Synthetic data only.** Generators in `tests/factories/` seeded per test; identifiers prefixed `SYN-`; emails `@example.test`.
2. **Seeds registry** `tests/seeds.py`: named constants for every stochastic test; a CI check forbids literal seeds elsewhere; tuning/test seed split by `seed mod 5`.
3. **Fixtures versioned in git:** `state_table.json`, `signing_vectors.json`, `qve_vectors.json`, detection corpora, payload corpora (+ `MANIFEST.sha256`), OpenAPI snapshot.
4. **Clocks:** injectable clock everywhere (`freezegun` or explicit `Clock` dependency); no `sleep` for synchronisation — poll with timeout ≤ 10 s.
5. **Environments:** `unit` (no services) · `ci` (compose services: Postgres, Redis; worker via Celery eager or real as marked) · `e2e` (full compose stack) · `staging` (post-deploy smoke only, plus Phase 8 security tests with explicit `--staging` flag). Tests refuse to run destructive actions unless `QS_ENV in {local, ci, staging-lab}`.
6. **Isolation:** each test module uses its own DB (template clone) and Redis DB index/prefix; parallelism via `pytest-xdist` only for modules marked parallel-safe.

---

## K. CI integration, quality gates and traceability
**Stages:** `lint/type → unit → quantum (fast) → integration (api + db) → security → web (unit/component/build) → e2e (path-filtered) → nightly (quantum slow, perf, dependency audits, full e2e) → release (everything + acceptance matrix)`.

**Gates (blocking on PR):** all fast stages green; coverage `backend/` ≥ 85%, `backend/quantum_engine/` ≥ 90%, `backend/api/auth/` and `backend/common/signing.py` ≥ 95%, web `src/lib` + `src/features` ≥ 80% (≥ 95% for `lib/ws`, `lib/safe`, `lib/auth`); Semgrep/gitleaks clean; OpenAPI drift check; acceptance-ID mapping check. **Blocking on release:** nightly suites green on the release commit; T-SEC-13/14 clear; acceptance matrix complete.

**Reporting:** JUnit XML + coverage artifacts per job; statistical campaign outputs (counts, CIs, seeds, versions) stored as artifacts and summarised in `docs/evaluation/results/`; flaky-test dashboard from CI history.

**Flake policy:** a test failing intermittently is quarantined within 24 h (marker `quarantine`, issue linked) and fixed before the next phase gate; no retries-to-green except for explicitly marked infrastructure-timing tests (max 1 retry, logged).

**Traceability (excerpt; full matrix generated by `scripts/check_acceptance_matrix.py`):**
| Acceptance ID | Verified by |
|---|---|
| Q-1, Q-2, Q-3 | T-Q-01, T-Q-02, T-Q-10, T-Q-11, T-Q-12 |
| Q-4, Q-5 | T-Q-03, T-Q-04 |
| Q-6, Q-7, Q-8 | T-Q-05, T-Q-06, T-Q-07, T-Q-08, T-Q-09 |
| Q-9 | T-Q-13 |
| Q-10 | T-Q-14 |
| Q-11, Q-12 | T-Q-15, T-LAB-15 |
| Q-13 | T-Q-16, T-DB-04, T-API-Q4, A.17 |
| Q-14, Q-15 | T-Q-06 (parser), T-Q-12, T-E2E-03 |
| SEC-1 … SEC-12 | T-SEC-01 … T-SEC-15, T-API-Z*, T-DB-08…12, T-FE-07 |
| LAB-1 … LAB-7 | T-LAB-01 … T-LAB-17 |
| API-1 … API-8 | T-API-*, T-FE-03, T-DB-01…03 |
| EVAL-1 … EVAL-8 | T-DET-*, T-API-EV*, T-E2E-03, T-FE-02 |
| ARC-1 … ARC-8 | T-DB-09/10, T-E2E-04…07, T-LAB-04, T-API-Q11, T-FE-04 |
| FE-G-*, FE-D*, FE-L* | T-FE-01 … T-FE-11 |

---

## L. Definition of done for testing, and common testing risks
**A feature's tests are done when:** (1) every acceptance ID it touches has a mapped, passing CI test; (2) positive, negative and fail-closed cases exist; (3) stochastic tests are seeded, tolerance-based, and documented with their SE budget; (4) no test depends on wall-clock time, network access, or another test's side effects; (5) coverage gates are met without trivial assertions; (6) the PR's Task Report lists the test IDs added.

| Risk | Symptom | Prevention |
|---|---|---|
| Vacuous noise tests | Noise tests pass although no noise was applied | Sanity assertion that noisy results differ from ideal by > 4 SE (T-Q-04, T-Q-13); `optimization_level=0` for labelled `id` gates |
| Seed-hunting | Seeds changed until tests pass | Re-baseline policy in §1.3; seeds only in `seeds.py`; PR review item |
| Over-tuned thresholds | Great detection on tuning data only | Disjoint test seeds; disjointness test (T-Q-15) |
| Little-endian/register bugs | Plausible but wrong fidelities | Named-register parser; branch-transform test T-Q-06 |
| Wrong oracle | Library validated against itself | Oracles computed independently (NumPy/Statevector in tests) |
| Teleportation via deferred measurement | Tests pass without classical feed-forward | Structural test + mutation tests T-Q-07 |
| Flaky async tests | Intermittent WS/job failures | Poll-with-timeout helpers; injectable clocks; quarantine policy |
| Tests mutating shared state | Order-dependent failures | Per-module DB clones; random test ordering in CI |
| Testing against third parties | Unauthorised traffic | Environment guard; Attack Lab only against registered sandboxes; ZAP only against own staging |
| Mixed `execution_kind` in reports | Misleading evaluation | Report validators (T-API-EV5) and UI stratification (FE-L09-2) |
