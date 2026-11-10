# QuantumShield — Quantum Protocol Specification

> Scope: simulation on Qiskit + Qiskit Aer with an abstraction that admits future hardware.
> All Qiskit fragments below are **specification sketches, not tested code**. Antigravity must write real tests from §12.

## 0. Notation and conventions

- Computational basis $|0\rangle=\begin{pmatrix}1\\0\end{pmatrix}$, $|1\rangle=\begin{pmatrix}0\\1\end{pmatrix}$.
- Pauli matrices $X=\begin{pmatrix}0&1\\1&0\end{pmatrix}$, $Y=\begin{pmatrix}0&-i\\i&0\end{pmatrix}$, $Z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}$.
- A single-qubit state has Bloch vector $\vec r=(\langle X\rangle,\langle Y\rangle,\langle Z\rangle)$ with $\rho=\tfrac12(I+\vec r\cdot\vec\sigma)$; pure states have $|\vec r|=1$.
- Measurement outcome bit `0` ↔ eigenvalue $+1$; bit `1` ↔ $-1$. Hence $P(0)=\tfrac12(1+\langle P\rangle)$ for a Pauli $P$.
- **Qiskit little-endian:** in a counts key `'q2 q1 q0'` the *leftmost* character is the highest-index classical bit. With multiple classical registers Qiskit prints registers separated by spaces, last-declared first. Parsers MUST use explicit register names and a unit test per layout.
- Gate matrices: $R_Y(\theta)=e^{-i\theta Y/2}=\begin{pmatrix}\cos\frac\theta2&-\sin\frac\theta2\\\sin\frac\theta2&\cos\frac\theta2\end{pmatrix}$, $R_Z(\varphi)=e^{-i\varphi Z/2}=\mathrm{diag}(e^{-i\varphi/2},e^{i\varphi/2})$.

---

## 1. Parameterised single-qubit state preparation

### 1.1 RY-only family

Initial state $|0\rangle$. Apply $R_Y(\theta)$:

$$|\psi(\theta)\rangle=R_Y(\theta)|0\rangle=\cos\tfrac\theta2\,|0\rangle+\sin\tfrac\theta2\,|1\rangle .$$

Computational-basis probabilities:

$$P(0)=\cos^2\tfrac\theta2=\tfrac12(1+\cos\theta),\qquad P(1)=\sin^2\tfrac\theta2=\tfrac12(1-\cos\theta).$$

Bloch vector: $\vec r=(\sin\theta,\;0,\;\cos\theta)$. The amplitudes are **real**, so the state lies in the $x$–$z$ great circle; $\langle Y\rangle=0$ for every $\theta$ (see §5.4).

**Encoding information.** A verifier-chosen $\theta$ is a real parameter; the probability $P(0)$ is a monotone function of $\theta\in[0,\pi]$. Given a measurement budget of $N$ shots, two parameters $\theta_a,\theta_b$ are statistically distinguishable at significance when

$$|P_a(0)-P_b(0)|\gtrsim 4\sqrt{\tfrac{1}{4N}}=\tfrac{2}{\sqrt N}.$$

For $N=1024$ this is $\approx 0.0625$, so the usable grid on $P(0)\in[0,1]$ has at most $\sim 16$ levels. This directly bounds the "information" a single measured setting can carry (≈ 4 bits) and is used in §9.4.

**Legitimate vs perturbed.** A perturbation replaces $|\psi\rangle$ by $\rho'=\mathcal E(|\psi\rangle\langle\psi|)$ or by a different pure state $|\psi'\rangle$. They are compared via

- fidelity $F=\langle\psi|\rho'|\psi\rangle=\tfrac12(1+\vec r\cdot\vec r')$ for pure $\psi$,
- measurement-statistics distance (§8).

### 1.2 Phase-sensitive extension: $R_Z(\varphi)R_Y(\theta)$

$$|\psi(\theta,\varphi)\rangle=R_Z(\varphi)R_Y(\theta)|0\rangle=e^{-i\varphi/2}\Big(\cos\tfrac\theta2|0\rangle+e^{i\varphi}\sin\tfrac\theta2|1\rangle\Big).$$

The prefactor $e^{-i\varphi/2}$ is a **global phase** (unobservable). The relative phase $e^{i\varphi}$ is observable only via bases that interfere $|0\rangle$ and $|1\rangle$.

$$\vec r=(\sin\theta\cos\varphi,\;\sin\theta\sin\varphi,\;\cos\theta).$$

**Why this matters.**
1. Z-basis statistics are independent of $\varphi$ — a phase-only forgery is invisible in Z.
2. RY-only has $\langle Y\rangle\equiv0$: a Y-basis measurement gives $P=\tfrac12$ regardless of $\theta$ and carries no discriminating information, so an RY-only scheme cannot detect perturbations that act as rotations about $Y$ or that act on the Y component.
3. Dephasing noise ($\langle X\rangle,\langle Y\rangle\to(1-2p)\langle\cdot\rangle$) is visible only in X/Y bases.

Therefore production verification MUST use the $(\theta,\varphi)$ family and all three bases. The RY-only family is retained only for baseline/regression tests.

### 1.3 Reference outcome probabilities (test vectors)

$P_Z(0)=\tfrac12(1+\cos\theta)$, $P_X(0)=\tfrac12(1+\sin\theta\cos\varphi)$, $P_Y(0)=\tfrac12(1+\sin\theta\sin\varphi)$.

| $\theta$ | $\varphi$ | $P_Z(0)$ | $P_X(0)$ | $P_Y(0)$ |
|---|---|---|---|---|
| 0 | any | 1 | 0.5 | 0.5 |
| $\pi$ | any | 0 | 0.5 | 0.5 |
| $\pi/2$ | 0 | 0.5 | 1 | 0.5 |
| $\pi/2$ | $\pi/2$ | 0.5 | 0.5 | 1 |
| $\pi/2$ | $\pi$ | 0.5 | 0 | 0.5 |
| $\pi/3$ | 0 | 0.75 | 0.9330 | 0.5 |
| $\pi/3$ | $\pi/2$ | 0.75 | 0.5 | 0.9330 |
| $\pi/4$ | $\pi/4$ | 0.8536 | 0.7500 | 0.7500 |

($\sin\frac\pi3=0.8660$; $\cos\frac\pi4=0.7071$; $\sin\frac\pi4\cos\frac\pi4=0.5$ so $P=0.75$; $P_Z=\tfrac12(1+0.7071)=0.8536$.)

### 1.4 Reference circuit (non-normative)

```python
from qiskit import QuantumCircuit

def prep_and_measure(theta: float, phi: float, basis: str) -> QuantumCircuit:
    qc = QuantumCircuit(1, 1)
    qc.ry(theta, 0)
    qc.rz(phi, 0)
    if basis == "X":
        qc.h(0)
    elif basis == "Y":
        qc.sdg(0); qc.h(0)      # S† then H maps |+i>→|0>, |-i>→|1>
    elif basis != "Z":
        raise ValueError(basis)
    qc.measure(0, 0)
    return qc
```

---

## 2. Bell-pair generation

Circuit on $q_0,q_1$ (both $|0\rangle$): $H$ on $q_0$, then $\mathrm{CNOT}(q_0\to q_1)$.

$$H|0\rangle\otimes|0\rangle=\tfrac{1}{\sqrt2}(|00\rangle+|10\rangle)\;\xrightarrow{\;\mathrm{CNOT}\;}\;|\Phi^+\rangle=\tfrac1{\sqrt2}(|00\rangle+|11\rangle).$$

Other Bell states: $|\Phi^-\rangle=\tfrac1{\sqrt2}(|00\rangle-|11\rangle)$, $|\Psi^\pm\rangle=\tfrac1{\sqrt2}(|01\rangle\pm|10\rangle)$.

**Expected correlations for $|\Phi^+\rangle$:**

| Basis pair | Outcomes | Expectation |
|---|---|---|
| ZZ | 00, 11 with ½ each; 01, 10 never | $\langle ZZ\rangle=+1$ |
| XX | same bits | $\langle XX\rangle=+1$ |
| YY | **opposite** bits | $\langle YY\rangle=-1$ |

(Z marginal of each qubit is uniform: $P(0)=\tfrac12$.)

**Entanglement test.** The projector onto $|\Phi^+\rangle$ is $\tfrac14(I+XX-YY+ZZ)$, hence

$$F_{\Phi^+}=\tfrac14\big(1+\langle XX\rangle-\langle YY\rangle+\langle ZZ\rangle\big).$$

For any separable state $F_{\Phi^+}\le\tfrac12$. **Entanglement witnessed iff $F_{\Phi^+}>\tfrac12$** (with the lower confidence bound above ½).

Optional CHSH check: with measurement angles for Alice $\{0,\pi/2\}$ and Bob $\{\pi/4,-\pi/4\}$ (in the $x$–$z$ plane) $S_{\max}=2\sqrt2$; any local hidden variable model gives $|S|\le 2$. For a Bell state mixed with white noise, $\rho=v|\Phi^+\rangle\langle\Phi^+|+(1-v)I/4$:

$$F_{\Phi^+}=\tfrac{1+3v}{4},\quad \text{entangled iff } v>\tfrac13,\quad S=2\sqrt2\,v,\quad\text{CHSH violation iff } v>\tfrac1{\sqrt2}\approx0.707 .$$

**Effect of noise** (independent single-qubit channels on the two halves, Pauli-diagonal):

| Channel (prob. $p$) | $\langle XX\rangle$ | $\langle YY\rangle$ | $\langle ZZ\rangle$ |
|---|---|---|---|
| Bit-flip on both | $\langle XX\rangle$ unchanged (1) | $\times(1-2p)^2$ | $\times(1-2p)^2$ |
| Phase-flip on both | $\times(1-2p)^2$ | $\times(1-2p)^2$ | unchanged (1) |
| Depolarizing (shrink $1-\lambda$ each) | $\times(1-\lambda)^2$ | $\times(1-\lambda)^2$ | $\times(1-\lambda)^2$ |

(Derivation: a Pauli error $P'$ on one qubit multiplies $\langle P\rangle$ by $-1$ if $P'$ anticommutes with $P$; an independent flip with probability $p$ gives a factor $1-2p$.) Readout error $\varepsilon$ (symmetric) multiplies each correlator by $(1-2\varepsilon)^2$.

---

## 3. Quantum teleportation

### 3.1 Registers

| Qubit | Role |
|---|---|
| $q_0$ | message qubit, state $|\psi\rangle=\alpha|0\rangle+\beta|1\rangle$ (Alice) |
| $q_1$ | Alice's half of the Bell pair |
| $q_2$ | Bob's half of the Bell pair |

Classical bits: $c_0$ (Alice's measurement of $q_0$), $c_1$ (Alice's measurement of $q_1$), $c_B$ (Bob's final verification measurement).

### 3.2 Circuit

1. Prepare $|\psi\rangle$ on $q_0$ via $R_Z(\varphi)R_Y(\theta)$.
2. Bell pair on $(q_1,q_2)$: $H(q_1)$; $\mathrm{CNOT}(q_1\to q_2)$.
3. Alice's Bell-basis measurement: $\mathrm{CNOT}(q_0\to q_1)$; $H(q_0)$; measure $q_0\to c_0$, $q_1\to c_1$.
4. **Classical transmission** of $(c_0,c_1)$ from Alice to Bob (2 classical bits; in the system this is a message through the API/worker, never "instantaneous").
5. **Feed-forward corrections on $q_2$:** if $c_1=1$ apply $X$; then if $c_0=1$ apply $Z$.
6. Bob's verification measurement: basis rotation then measure $q_2\to c_B$.

### 3.3 Derivation

Initial state:
$$|\Psi_0\rangle=(\alpha|0\rangle+\beta|1\rangle)_0\otimes\tfrac1{\sqrt2}(|00\rangle+|11\rangle)_{12}
=\tfrac1{\sqrt2}\big[\alpha|000\rangle+\alpha|011\rangle+\beta|100\rangle+\beta|111\rangle\big].$$

After $\mathrm{CNOT}(q_0\to q_1)$ (flip $q_1$ when $q_0=1$):
$$|\Psi_1\rangle=\tfrac1{\sqrt2}\big[\alpha|000\rangle+\alpha|011\rangle+\beta|110\rangle+\beta|101\rangle\big].$$

After $H$ on $q_0$ ($H|0\rangle=\tfrac{|0\rangle+|1\rangle}{\sqrt2}$, $H|1\rangle=\tfrac{|0\rangle-|1\rangle}{\sqrt2}$):
$$|\Psi_2\rangle=\tfrac12\big[\alpha(|0\rangle+|1\rangle)|00\rangle+\alpha(|0\rangle+|1\rangle)|11\rangle+\beta(|0\rangle-|1\rangle)|10\rangle+\beta(|0\rangle-|1\rangle)|01\rangle\big].$$

Group by Alice's outcomes $(m_0,m_1)$ for $(q_0,q_1)$:

$$|\Psi_2\rangle=\tfrac12\Big[\,|00\rangle(\alpha|0\rangle+\beta|1\rangle)+|01\rangle(\alpha|1\rangle+\beta|0\rangle)+|10\rangle(\alpha|0\rangle-\beta|1\rangle)+|11\rangle(\alpha|1\rangle-\beta|0\rangle)\Big]$$

where the kets $|m_0m_1\rangle$ are Alice's and the bracketed state is Bob's $q_2$. Recognising $X|\psi\rangle=\alpha|1\rangle+\beta|0\rangle$, $Z|\psi\rangle=\alpha|0\rangle-\beta|1\rangle$, $XZ|\psi\rangle=\alpha|1\rangle-\beta|0\rangle$:

| $(m_0,m_1)$ | Probability | Bob's state before correction |
|---|---|---|
| 00 | ¼ | $|\psi\rangle$ |
| 01 | ¼ | $X|\psi\rangle$ |
| 10 | ¼ | $Z|\psi\rangle$ |
| 11 | ¼ | $XZ|\psi\rangle$ |

In general Bob holds $X^{m_1}Z^{m_0}|\psi\rangle$. The inverse is $(X^{m_1}Z^{m_0})^{-1}=Z^{m_0}X^{m_1}$, so Bob applies **$X^{m_1}$ first, then $Z^{m_0}$**. This restores $|\psi\rangle$ exactly in all four branches. Because $ZX=-XZ$, applying the two corrections in the opposite order would differ only by a global phase of $-1$: physically unobservable, but the order above is fixed so that statevector-equality tests need no phase special-casing (and tests must still compare via $|\langle\psi|\phi\rangle|^2$).

**No-signalling check.** Before correction, Bob's reduced state averaged over outcomes is $\tfrac14\sum P|\psi\rangle\langle\psi|P^\dagger=\tfrac I2$ (Pauli twirl). Bob learns nothing without the two classical bits; teleportation cannot carry information faster than the classical channel. A test MUST demonstrate this: omit corrections ⇒ Bob's Bloch vector $\to\vec0$ (fidelity $\tfrac12$).

### 3.4 Reference circuit (non-normative)

```python
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

def teleport(theta, phi, basis):
    q = QuantumRegister(3, "q")
    c0 = ClassicalRegister(1, "c0")   # outcome of q0 (→ Z correction)
    c1 = ClassicalRegister(1, "c1")   # outcome of q1 (→ X correction)
    cb = ClassicalRegister(1, "cb")   # Bob's verification bit
    qc = QuantumCircuit(q, c0, c1, cb)
    qc.ry(theta, 0); qc.rz(phi, 0)    # |ψ> on q0
    qc.h(1); qc.cx(1, 2)              # Bell pair
    qc.barrier()
    qc.cx(0, 1); qc.h(0)
    qc.measure(0, c0[0]); qc.measure(1, c1[0])
    with qc.if_test((c1, 1)): qc.x(2) # X first
    with qc.if_test((c0, 1)): qc.z(2) # then Z
    qc.barrier()
    if basis == "X": qc.h(2)
    elif basis == "Y": qc.sdg(2); qc.h(2)
    qc.measure(2, cb[0])
    return qc
```
The coherent "deferred-measurement" variant (`cx(1,2); cz(0,2)` instead of measurements + `if_test`) MAY be used **only** as a cross-check; it is not a teleportation protocol because it has no classical communication.

### 3.5 Verifying the reconstruction

*State tomography on Bob's qubit.* Run the circuit three times (basis $=X,Y,Z$), $N$ shots each, discard $(c_0,c_1)$. Estimate $\hat r_i=1-2\hat p_i(1)$, i.e. $\hat r_i=2\hat p_i(0)-1$. Fidelity with the pure target $\vec r_t$:

$$\hat F=\tfrac12\big(1+\hat{\vec r}\cdot\vec r_t\big),\qquad \sigma_F\approx\tfrac12\sqrt{\sum_i r_{t,i}^2\,\frac{1-\hat r_i^2}{N}}\le\tfrac12\sqrt{\tfrac{2/3}{N}}.$$

(For $N=4096$ per basis, worst-case $\sigma_F\approx0.0064$.)

*Global phase.* Fidelity $|\langle\psi|\phi\rangle|^2$ and Bloch vectors are global-phase invariant. If a statevector comparison is done in a unit test (e.g. Aer `save_statevector` for the unconditional deferred-measurement variant), it MUST compare $|\langle\psi|\phi\rangle|^2$, never amplitudes element-wise.

*Pass criteria.*
- Ideal simulator, $N=4096$/basis: $\hat F\ge0.98$ (≈3σ margin at worst case) **and** the four $(c_0,c_1)$ outcomes each within a 99.9% binomial interval of ¼.
- Noisy simulator: $\hat F\ge F_{\text{cal}}-4\sigma_F$, where $F_{\text{cal}}$ is the calibrated expectation for the same circuit family.
- Quantum-advantage benchmark: the *average* fidelity over the six states $\{\pm X,\pm Y,\pm Z\}$ must exceed the **classical measure-and-prepare limit of $2/3$** to claim that the channel is better than any classical channel could be for unknown qubit states (a single known state can be "faked" classically with $F=1$; this limit only applies to the unknown-state average).

---

## 5. Measurement

### 5.1 Computational (Z) basis
Measure directly. $P(0)=|\langle0|\psi\rangle|^2$.

### 5.2 X basis
Apply $H$, then measure Z. $H$ maps $|\pm\rangle\to|0\rangle,|1\rangle$. $P_X(0)=|\langle+|\psi\rangle|^2=\tfrac12(1+\langle X\rangle)$.

### 5.3 Y basis
Apply $S^\dagger$ then $H$, then measure Z. Check: $|{+i}\rangle=\tfrac{|0\rangle+i|1\rangle}{\sqrt2}\xrightarrow{S^\dagger}\tfrac{|0\rangle+|1\rangle}{\sqrt2}=|+\rangle\xrightarrow{H}|0\rangle$. $P_Y(0)=\tfrac12(1+\langle Y\rangle)$.

### 5.4 Why RY-only fails in the Y basis
For $|\psi\rangle=\cos\frac\theta2|0\rangle+\sin\frac\theta2|1\rangle$,
$\langle Y\rangle=\langle\psi|Y|\psi\rangle=2\,\mathrm{Im}(a^*b)=0$ for real $a,b$. So $P_Y(0)=\tfrac12$ for all $\theta$: the Y measurement returns a fair coin for every legitimate state, hence cannot *discriminate* parameters; it is useful only as a **null-hypothesis check** (a nonzero $\langle Y\rangle$ signals tampering with phase).

### 5.5 Shots and statistics
- Counts $n_0+n_1=N$; $\hat p=n_0/N$; $\mathrm{SE}=\sqrt{\hat p(1-\hat p)/N}$.
- Default $N=1024$ for verification settings, $N=8192$ for calibration, $N=4096$ for tomography.
- Wilson 95% interval: $\dfrac{\hat p+\frac{z^2}{2N}\pm z\sqrt{\frac{\hat p\hat q}{N}+\frac{z^2}{4N^2}}}{1+\frac{z^2}{N}}$.
- Seeds: simulator seed MUST be stored; ideal-simulator verification tests are seeded and thus reproducible.

---

## 6. Noise models (Aer)

### 6.1 Single-qubit channels

| Model | Kraus / Pauli form | Bloch-vector action |
|---|---|---|
| Bit flip (prob. $p$) | $\rho\to(1-p)\rho+pX\rho X$ | $(r_x,\,(1-2p)r_y,\,(1-2p)r_z)$ |
| Phase flip (prob. $p$) | $\rho\to(1-p)\rho+pZ\rho Z$ | $((1-2p)r_x,\,(1-2p)r_y,\,r_z)$ |
| Depolarizing (param. $\lambda$) | $\rho\to(1-\lambda)\rho+\lambda\tfrac I2$ | $(1-\lambda)\vec r$ |
| Readout error ($\varepsilon_0=P(1|0)$, $\varepsilon_1=P(0|1)$) | classical post-processing | $p_0'=(1-\varepsilon_0)p_0+\varepsilon_1(1-p_0)$ |

Relation: Aer's `depolarizing_error(λ, n)` uses $\rho\to(1-\lambda)\rho+\lambda I/2^n$; if one wants each of $X,Y,Z$ with probability $p/3$, then $\lambda=4p/3$ (single qubit).

### 6.2 Aer construction (non-normative)

```python
from qiskit_aer.noise import NoiseModel, pauli_error, depolarizing_error, ReadoutError

def build_noise(p_bitflip=0.0, p_phaseflip=0.0, lam_1q=0.0, lam_2q=0.0, e0=0.0, e1=0.0):
    nm = NoiseModel()
    one_q = ["ry", "rz", "h", "x", "z", "sdg", "id"]
    err = None
    if p_bitflip:   err = pauli_error([("X", p_bitflip), ("I", 1 - p_bitflip)])
    if p_phaseflip: 
        e = pauli_error([("Z", p_phaseflip), ("I", 1 - p_phaseflip)])
        err = e if err is None else err.compose(e)
    if lam_1q:
        e = depolarizing_error(lam_1q, 1)
        err = e if err is None else err.compose(e)
    if err is not None: nm.add_all_qubit_quantum_error(err, one_q)
    if lam_2q: nm.add_all_qubit_quantum_error(depolarizing_error(lam_2q, 2), ["cx"])
    if e0 or e1: nm.add_all_qubit_readout_error(ReadoutError([[1 - e0, e0], [e1, 1 - e1]]))
    return nm
```
Circuits MUST be transpiled to the noise model's basis gates before execution. The noise model's canonical JSON (`nm.to_dict()` sorted) is hashed; the hash is stored as `noise_model_hash`.

### 6.3 Default noise profiles (for experiments)

| Profile | Parameters |
|---|---|
| `clean` | none (ideal) |
| `lab-low` | $\lambda_{1q}=0.001$, $\lambda_{2q}=0.01$, $\varepsilon_0=\varepsilon_1=0.01$ |
| `lab-medium` | $\lambda_{1q}=0.003$, $\lambda_{2q}=0.03$, $\varepsilon_0=\varepsilon_1=0.02$ |
| `lab-high` | $\lambda_{1q}=0.01$, $\lambda_{2q}=0.08$, $\varepsilon_0=\varepsilon_1=0.04$ |
| `dephasing-stress` | $p_{\text{phase}}=0.03$ |

Parameters are *synthetic*; they do not describe any real device and MUST NOT be presented as such.

---

## 7. Calibration and baseline collection

**Purpose:** estimate the honest-channel distribution so verification can tolerate legitimate noise.

1. **Circuit families calibrated separately:** `direct` (prepare+measure) and `teleport` (3-qubit). Each uses the same settings grid.
2. **Settings:** for each family, all $(\theta,\varphi,\text{basis})$ in the *verification grid* (§9.2) — at most 9 θ × 8 φ × 3 bases = 216 settings; redundant settings (RY-only duplicates, e.g. φ irrelevant at θ=0,π) are merged.
3. **Windows:** $K_w=5$ independent windows (separate seeds; in hardware, separate times), each with $N_{\text{cal}}=8192$ shots/setting.
4. **Estimates:** pooled $\bar p_s=\sum_w n_{s,w}/(K_wN_{\text{cal}})$.
5. **Over-dispersion check** (detects drift or mis-specified noise): $D_s=\sum_w\frac{(n_{s,w}-N_{\text{cal}}\bar p_s)^2}{N_{\text{cal}}\bar p_s\bar q_s}\sim\chi^2_{K_w-1}$. If $p<0.01$: set variance inflation $\phi_s=D_s/(K_w-1)$, else $\phi_s=1$.
6. **Validity:** a calibration record is `VALID` for 24 h (simulation: until the noise-profile hash changes) and `STALE` afterwards. Verification against a `STALE` record returns `INCONCLUSIVE`.
7. **Ideal backend:** no empirical calibration — expected probabilities are analytic ($\S1.3$). Calibration code is still run against the *noisy simulator* and compared with analytic noisy expectations as a self-test of the calibration pipeline (acceptance: all $|\bar p_s-p_s^{\text{analytic}}|<4\,\mathrm{SE}$).

---

## 8. Quantum verification: statistical methodology

### 8.1 Hypotheses
For each verification setting $s=1..m$: $H_0$: the observed counts were produced by the calibrated honest channel for the expected state; $H_1$: otherwise.

### 8.2 Expected distribution
$$p_s^{\text{exp}}=\begin{cases}\text{analytic } p_s&\text{ideal backend}\\ \bar p_s^{\text{cal}}&\text{noisy / hardware (empirical baseline)}\end{cases}$$

### 8.3 Per-setting test
Pearson statistic with $E_{s,j}=N p^{\text{exp}}_{s,j}$:
$$X_s^2=\frac1{c}\sum_{j\in\{0,1\}}\frac{(O_{s,j}-E_{s,j})^2}{E_{s,j}},\qquad c=\phi_s\Big(1+\tfrac{N}{K_wN_{\text{cal}}}\Big)$$
The factor $c$ accounts for the fact that the baseline is itself estimated (variance of $n_0-N\bar p$ is $Np q\,(1+N/N_{\text{base}})$) and for over-dispersion. Under $H_0$, $X_s^2\approx\chi^2_1$.

**Validity condition (expected-count rule):** every $E_{s,j}\ge5$. If violated (e.g., $p^{\text{exp}}\approx0$ or 1), do **not** use $\chi^2$; use the exact two-sided binomial test with the baseline Wilson upper bound of the expected error rate (for $p^{\rm exp}\in\{0,1\}$ any error count above $\text{Binom}^{-1}$ at the chosen tail is a rejection). Cells are never "merged away" silently: the verdict records which test was used per setting.

### 8.4 Aggregate test
Settings are independent (different circuits/seeds), so
$$X_{\text{tot}}^2=\sum_{s\in\mathcal S_{\chi}}X_s^2\;\sim\;\chi^2_{|\mathcal S_\chi|}.$$
Reject $H_0$ if $p_{\text{tot}}<\alpha_{\text{tot}}$ (default $10^{-3}$). In addition run a **localised-deviation test**: reject if $\max_s|z_s|>z_{1-\alpha_{\max}/(2m)}$ (Bonferroni, $\alpha_{\max}=10^{-3}$), with $z_s=\dfrac{O_{s,0}-Np_s}{\sqrt{c\,Np_sq_s}}$. The overall false-reject rate on honest channels is therefore $\le\alpha_{\text{tot}}+\alpha_{\max}\approx2\times10^{-3}$ (union bound).

### 8.5 Power / sample size
For one binary setting to detect a shift $\delta$ with significance $\alpha$ and power $1-\beta$:
$$N\ge\left(\frac{z_{1-\alpha/2}\sqrt{p_0q_0}+z_{1-\beta}\sqrt{p_1q_1}}{\delta}\right)^2 .$$
Worked example: $p_0=0.5,\ p_1=0.55,\ \alpha=10^{-3}\ (z=3.2905),\ \beta=0.1\ (z=1.2816)$: $N\ge\big((1.6452+0.6376)/0.05\big)^2\approx2085$ shots. The aggregate test has non-central $\chi^2_m(\lambda)$ distribution with $\lambda=\sum_sN\delta_s^2/(p_sq_s)$; the evaluation module MUST compute achieved power numerically (`scipy.stats.ncx2`) for each configured $m,N,\alpha$ and record it in the experiment report.

### 8.6 Distinguishing noise from manipulation
$\chi^2$ rejection alone says "not the calibrated channel". The classifier then performs a **structure analysis** on the Bloch-vector estimates. Group settings by $(\theta,\varphi)$ so that X/Y/Z estimates give $\hat{\vec r}_k$ for each state $k$, with calibrated expected vector $\vec r^{\,\text{exp}}_k$.

1. **Contraction fit** (noise-like): $\hat\kappa=\dfrac{\sum_k\hat{\vec r}_k\cdot\vec r^{\,\text{exp}}_k}{\sum_k|\vec r^{\,\text{exp}}_k|^2}$. Re-run the aggregate test with expectation $\hat\kappa\,\vec r^{\,\text{exp}}$. If this *passes* and $\hat\kappa\in[\kappa_{\min},1]$ (default $\kappa_{\min}=0.90$) ⇒ classification **`NOISE_DRIFT`** (verdict `INCONCLUSIVE`, trigger recalibration).
2. **Direction error:** $\psi_k=\arccos\dfrac{\hat{\vec r}_k\cdot\vec r^{\,\text{exp}}_k}{|\hat{\vec r}_k||\vec r^{\,\text{exp}}_k|}$. A median $\psi$ exceeding $\psi_{\text{tol}}$ (≈ 4 SE-equivalent, computed per run) indicates a **unitary-like tamper** (e.g. over-rotation).
3. **Anisotropy:** per-axis contraction $\hat\kappa_x,\hat\kappa_y,\hat\kappa_z$. Intercept–resend in Z gives $\hat\kappa_z\approx1,\ \hat\kappa_x,\hat\kappa_y\approx0$; an honest depolarizing channel gives $\kappa_x\approx\kappa_y\approx\kappa_z$; honest bit-flip gives $\kappa_x\approx1,\kappa_y\approx\kappa_z$.
4. Rules: significant direction error **or** significant anisotropy not explained by the calibrated noise's own anisotropy ⇒ **`CHANNEL_MANIPULATION`** (verdict `FAIL`).

> **Honest limitation:** an attacker whose action is *indistinguishable from the calibrated noise* (e.g. adds only an isotropic contraction with $\kappa\ge\kappa_{\min}$) is not detectable by this method. The tolerance $\kappa_{\min}$ defines the **noise budget**: the verifier accepts any channel at least as good as $\kappa_{\min}$. This is the residual risk and MUST be reported in every channel-manipulation evaluation.

### 8.7 Thresholds, FAR and FRR
- $\text{FRR}=P(\text{verdict}\ne\text{PASS}\mid\text{honest})$; $\text{FAR}=P(\text{PASS}\mid\text{tamper},\text{intensity }\iota)$.
- Select $\alpha_{\text{tot}}$ on **honest calibration data only** (never tuned on the attack set that is later used for evaluation — train/test split of seeds).
- Report: ROC over $\alpha\in\{10^{-1},\dots,10^{-6}\}$; FAR at the operating point for each attack type and intensity; `INCONCLUSIVE` rate separately (it counts as non-accept on `BLOCKING` resources).
- **Sequential retries inflate error rates.** Retries MUST use fresh nonce/parameters; with $r$ allowed retries and "accept if any pass", FAR can grow by up to $r$; allowed retries ≤ 1, and the combined decision uses alpha-spending ($\alpha/2$ per attempt).

### 8.8 Verdict logic

```
if precondition_failed (stale calibration, backend unhealthy, E<5 for all settings) → INCONCLUSIVE
elif aggregate_reject or localised_reject:
     if structure == NOISE_DRIFT → INCONCLUSIVE (recalibrate)
     else → FAIL (classification = CHANNEL_MANIPULATION | EVIDENCE_MISMATCH)
else → PASS
```

---

## 9. Quantum Verification Evidence (QVE) protocol

This section defines what "quantum-assisted signature / verification evidence" means in QuantumShield, in a way that is honest about what a *simulation* can establish.

### 9.1 Roles and secrets
- Enrolment (classical, out of band): Defender and a protected identity share a 256-bit secret $K_q$ (separate from the HMAC request key $K_{\text{req}}$). Stored encrypted (envelope encryption), never logged.
- **Quantum worker** is a trusted component running circuits for a "link" (Alice = protected app side, Bob = verifier side) through a **channel profile** (clean, noise profile, or attacker operation).

### 9.2 Challenge derivation
Given canonical request digest $d=\mathrm{SHA256}(\text{canonical string})$ and nonce $n$:
$$\text{stream}=\mathrm{HKDF\text{-}SHA256}(K_q,\ \text{salt}=n,\ \text{info}=\texttt{"QS-QVE-v1"}\,\|\,d)$$
For $j=1..m$ (default $m=24$): consume 12 bits → $\theta_j=\tfrac{k_\theta\pi}{8}$ with $k_\theta\in\{0..8\}$ (via rejection sampling for uniformity), $\varphi_j=\tfrac{k_\varphi\pi}{4}$ with $k_\varphi\in\{0..7\}$, basis $b_j\in\{X,Y,Z\}$. Avoid settings with $p\in\{0,1\}$ unless intentionally included as null checks (≤ 4 of $m$).

### 9.3 Evidence object
$$\mathrm{QVE}=\{\text{request\_id},\ \text{family},\ \text{params\_digest},\ \text{backend descriptor},\ \text{counts}_{1..m},\ \text{seed},\ \text{noise\_model\_hash},\ \text{calibration\_id},\ \text{mac}\}$$
with $\text{mac}=\mathrm{HMAC}_{K_q}(\text{canonical JSON of all fields except mac})$ and `evidence_digest=SHA256(canonical JSON)`.

### 9.4 Verification steps (all MUST pass)
1. MAC valid (constant-time compare).
2. `params_digest` equals the digest recomputed from $K_q,d,n$ ⇒ evidence is bound to *this* request (blocks cross-request reuse).
3. Backend descriptor consistent: `execution_kind` ∈ allowed set for the resource; Aer never claims hardware.
4. `evidence_digest` unseen (duplicate ⇒ `REPLAY`).
5. Statistical verdict from §8.

**Bound on guessing (forger without $K_q$).** If the forger must produce counts for unknown parameters, per setting it must hit the right grid cell on $P(0)$; with $L_{\text{eff}}\approx16$ distinguishable levels at $N=1024$ (§1.1) the per-setting success is $\approx 2^{-4}$ and for $m=24$ roughly $2^{-96}$ — but the real protection is the MAC and parameter derivation under $K_q$ (computational, HMAC-SHA256). The quantum statistics supply *no additional information-theoretic security* in simulation.

### 9.5 Decision combination
| Classical (signature/nonce/time/session) | Quantum verdict | Final |
|---|---|---|
| REJECT | any | **REJECT** |
| ACCEPT | PASS | ACCEPT |
| ACCEPT | FAIL | **REJECT** + incident |
| ACCEPT | INCONCLUSIVE | `BLOCKING`: REJECT/step-up; `MONITOR`: ACCEPT + flag |

### 9.6 Channel manipulation models (Attack Lab inserts these in the "channel" segment)
Inserted between preparation and measurement (direct family) or on the transported qubit / Bell pair (teleport family):

| Name | Operation | Bloch action | Detectable via |
|---|---|---|---|
| `intercept_resend_Z` | measure Z, re-prepare | $(0,0,r_z)$ | X,Y contraction → 0 |
| `intercept_resend_random` | measure random of X/Y/Z, re-prepare | partial collapse, average contraction ≈ 1/3 | all axes |
| `over_rotation_Y(ε)` | $R_Y(\varepsilon)$ | rotates $x\!-\!z$ | direction error |
| `phase_kick(ε)` | $R_Z(\varepsilon)$ | rotates $x\!-\!y$ | direction error in X/Y (invisible in Z) |
| `depolarize(λ)` | isotropic noise | $(1-\lambda)\vec r$ | noise-like; only detected if $1-\lambda<\kappa_{\min}$ |
| `bellpair_decohere(v)` | white noise on shared pair | teleport fidelity $\frac{1+v}{2}$ | tomography fidelity drops |

(For teleportation with a Bell pair of visibility $v$, the output Bloch vector is $v\,\vec r$, so $F=\tfrac{1+v}{2}$; classical bound $2/3$ is beaten only if $v>\tfrac13$.)

---

## 10. Quantum backend abstraction

```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence, Mapping

class ExecutionKind(str, Enum):
    IDEAL_SIMULATOR = "IDEAL_SIMULATOR"
    NOISY_SIMULATOR = "NOISY_SIMULATOR"
    PHYSICAL_HARDWARE = "PHYSICAL_HARDWARE"

@dataclass(frozen=True)
class BackendDescriptor:
    backend_id: str                  # e.g. "aer-ideal-1", "aer-noisy-lab-low"
    execution_kind: ExecutionKind
    provider: str                    # "qiskit-aer" | "ibm-quantum" | ...
    provider_job_id: str | None      # REQUIRED iff PHYSICAL_HARDWARE
    qiskit_version: str
    aer_version: str | None
    noise_model_hash: str | None     # REQUIRED iff NOISY_SIMULATOR
    seed: int | None
    supports_dynamic_circuits: bool
    n_qubits: int

@dataclass(frozen=True)
class CircuitResult:
    counts: Mapping[str, int]        # keys by register-aware format
    shots: int
    descriptor: BackendDescriptor
    transpile_info: dict

class QuantumBackend(Protocol):
    def descriptor(self) -> BackendDescriptor: ...
    def health(self) -> dict: ...
    def run(self, circuits: Sequence["QuantumCircuit"], shots: int, *,
            seed: int | None, timeout_s: float) -> list[CircuitResult]: ...
```

**Invariants (enforced by validators, DB `CHECK`s and API schema tests):**
1. `execution_kind=PHYSICAL_HARDWARE ⇒ provider_job_id IS NOT NULL ∧ provider ≠ 'qiskit-aer'`.
2. `provider='qiskit-aer' ⇒ execution_kind ∈ {IDEAL_SIMULATOR, NOISY_SIMULATOR}`.
3. `NOISY_SIMULATOR ⇒ noise_model_hash IS NOT NULL`.
4. Every API response, report, and UI card that shows a quantum result displays the `execution_kind` badge. Reports mixing kinds are rejected unless stratified.
5. Calibrations are keyed by `(backend_id, circuit_family, noise_model_hash)` and never reused across keys.

**Requirements for real hardware (future):**
- Transpile to the device's native gates and coupling map; record the transpiled depth and two-qubit gate count.
- **Dynamic circuits:** mid-circuit measurement and feed-forward (the $X/Z$ corrections) are not available on all devices; if `supports_dynamic_circuits=False`, teleportation with real classical feed-forward cannot be run and the system must say so rather than silently using the deferred-measurement variant.
- Queue latency (minutes to hours) ⇒ asynchronous only; `BLOCKING` resources cannot use hardware-gated verification in real time.
- Calibration must be refreshed per device calibration cycle; gate/readout errors drift.
- Credentials via secret manager; shot/cost budgets; provider results validated and size-capped.
- Error mitigation, if used, MUST be labelled and reported separately from raw results.

---

## 11. Scientific limitations (mandatory reading for all contributors)

1. **What teleportation demonstrates:** transfer of an unknown qubit state between two locations using one shared entangled pair plus two classical bits. The original state is destroyed (no-cloning); no information moves faster than light.
2. **What it is not:** it does not encrypt, authenticate, or integrity-protect classical data. It does not transmit classical bits "for free".
3. **HTTP:** Ordinary HTTP/TLS traffic is classical data over classical networks. A quantum circuit in a Python process cannot protect it. Protection comes from TLS, authentication, authorization, and input validation.
4. **PostgreSQL:** circuits do not secure a database. Access control, encryption at rest, network isolation, backups, and RLS do.
5. **What a simulator can show:** correctness of protocol logic, behaviour under *modelled* noise, the statistical power of detection tests against *modelled* attacks. It cannot show security against real adversaries or real device behaviour.
6. **What real quantum security requires:** physical quantum channels and devices (e.g., QKD such as BB84/E91, quantum digital signatures), whose security proofs rely on no-cloning and measurement disturbance under specific device assumptions. QuantumShield does **not** implement or claim that.
7. **Authentication of the classical channel:** teleportation and QKD both require an authenticated classical channel; otherwise a man-in-the-middle is possible. Here that is provided by the classical layer.

**Scientifically meaningful experiments**
- Verification statistics: FAR/FRR vs. noise profile and tamper intensity, with confidence intervals.
- Teleportation fidelity vs. noise, benchmarked against the $2/3$ classical limit (six-state average).
- Bell-pair witness $F_{\Phi^+}>\tfrac12$ and CHSH vs. noise.
- Detection of phase-only perturbations: comparison of RY-only vs. $(\theta,\varphi)$ families (expected: RY-only misses phase kicks).
- Calibration-drift robustness (over-dispersion handling).

**Misleading experiments (MUST NOT be presented as results)**
- "Quantum-secured HTTP/DB" demonstrations.
- Success rates on a single state / single seed.
- Reporting Aer outcomes as hardware or as "real quantum".
- Tuning thresholds on the same attack data used for reporting.
- Claiming security against an adversary who holds $K_q$ or $K_{\text{req}}$.
- Comparing detection rates without stating the noise-budget (depolarizing attacker within tolerance).

---

## 12. Acceptance criteria and test vectors

| ID | Test | Pass condition |
|---|---|---|
| Q-1 | State prep table §1.3, ideal statevector | Max abs error < 1e-12 for all rows |
| Q-2 | Sampling §1.3, $N=8192$, seeded | Each $\hat p$ within 4 SE of table value |
| Q-3 | RY-only Y-basis | $\hat P_Y(0)$ within 4 SE of 0.5 for θ ∈ {0, π/4, π/2, π} |
| Q-4 | Bell pair, ideal | $P(01)+P(10)=0$ exactly; XX, ZZ = +1, YY = −1 |
| Q-5 | Bell witness, `lab-medium` | Lower 99% bound of $F_{\Phi^+}>0.5$; matches analytic prediction within 4 SE |
| Q-6 | Teleportation, ideal, 6 states, N=4096 | $\hat F\ge0.98$ each; outcomes $(c_0,c_1)$ uniform (χ² p>0.001) |
| Q-7 | Teleportation without corrections | Bloch vector norm < 4·SE; $\hat F\in[0.5\pm4\sigma]$ |
| Q-8 | Missing-correction negative tests | Dropping only the Z correction flips $r_x,r_y$ (detected for states with $r_x$ or $r_y\ne0$); dropping only the X correction flips $r_y,r_z$; swapping X/Z order changes nothing observable (global phase only) |
| Q-9 | Noise algebra §6.1 | Empirical Bloch contraction within 4 SE of analytic for bit-flip, phase-flip, depolarizing, readout |
| Q-10 | Calibration self-test | See §7.7 |
| Q-11 | Honest verification, 2 000 trials/profile | Observed FRR ≤ 0.5% with 95% upper bound ≤ 1% |
| Q-12 | Tamper library §9.6 at documented intensities | Report FAR with Wilson CI; intercept-resend-Z FAR ≤ 0.1% |
| Q-13 | Provenance invariants §10 | Constructing an invalid descriptor raises; DB insert violating `CHECK` fails |
| Q-14 | Endianness | Parser round-trip test across single-register, multi-register circuits |
| Q-15 | Reproducibility | Same seed ⇒ identical counts; different seed ⇒ statistically consistent counts |
