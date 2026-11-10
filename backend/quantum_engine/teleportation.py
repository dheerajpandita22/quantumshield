"""
QuantumShield Quantum Engine — Quantum Teleportation Protocol

Implements the full quantum teleportation circuit using Qiskit.
Teleportation transmits a quantum state from Alice to Bob using:
  - 1 pre-shared Bell pair
  - 2 classical bits communicated from Alice to Bob
  - 2 measurement-conditioned corrections on Bob's qubit

IMPORTANT DISCLAIMER:
  Quantum teleportation transfers a *quantum state*, not classical information
  or data. It does not violate causality (classical bits are still required).
  It does NOT protect HTTP requests, databases, or classical network traffic.
  It is relevant to future quantum-authenticated channels and QKD schemes.

Qubit layout (3-qubit circuit):
  q[0] = Alice's data qubit (the state to teleport)
  q[1] = Alice's half of the Bell pair
  q[2] = Bob's half of the Bell pair (receives the teleported state)

Classical bits:
  c[0] = Alice's measurement of q[1] → controls Bob's X gate
  c[1] = Alice's measurement of q[0] → controls Bob's Z gate
  c[2] = Bob's final measurement of q[2] (verification, not part of protocol)
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import Initialize
from qiskit_aer import AerSimulator

from backend.quantum_engine.state_preparation import prepare_ry_state, expected_statevector
from backend.quantum_engine.bell_pair import generate_bell_pair, BellState


def build_teleportation_circuit(theta: float, phi: float = 0.0) -> QuantumCircuit:
    """
    Builds the complete quantum teleportation circuit for a state
    |ψ⟩ = cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩.

    The circuit implements:
    1. State preparation on q[0]
    2. Bell pair generation on q[1], q[2]
    3. Bell-basis measurement of q[0], q[1] by Alice
    4. Measurement-conditioned X correction (from c[0]) on q[2]
    5. Measurement-conditioned Z correction (from c[1]) on q[2]

    Classical feed-forward is implemented via Qiskit's if_test (c_if)
    mechanism, which is natively supported by Aer simulators.

    Args:
        theta: Polar angle of the state to teleport (radians).
        phi:   Azimuthal phase angle (radians). Default 0.0 (real state).

    Returns:
        A QuantumCircuit with 3 qubits and 3 classical bits.
    """
    # Registers
    qr = QuantumRegister(3, "q")
    cr_alice = ClassicalRegister(2, "alice")  # Alice's measurement results
    cr_bob = ClassicalRegister(1, "bob")      # Bob's verification measurement
    qc = QuantumCircuit(qr, cr_alice, cr_bob, name="teleportation")

    # ------------------------------------------------------------------
    # Step 1: Prepare the state to teleport on q[0]
    # ------------------------------------------------------------------
    qc.ry(theta, qr[0])
    if abs(phi) > 1e-10:
        qc.p(phi, qr[0])  # Phase gate: |1⟩ → e^{iφ}|1⟩
    qc.barrier(label="state_prep")

    # ------------------------------------------------------------------
    # Step 2: Generate Bell pair |Φ+⟩ on q[1] and q[2]
    # ------------------------------------------------------------------
    qc.h(qr[1])
    qc.cx(qr[1], qr[2])
    qc.barrier(label="bell_pair")

    # ------------------------------------------------------------------
    # Step 3: Alice's Bell-basis measurement of q[0] and q[1]
    # ------------------------------------------------------------------
    qc.cx(qr[0], qr[1])
    qc.h(qr[0])
    qc.barrier(label="bell_basis_meas")
    qc.measure(qr[1], cr_alice[0])  # c_alice[0] controls X on Bob
    qc.measure(qr[0], cr_alice[1])  # c_alice[1] controls Z on Bob

    # ------------------------------------------------------------------
    # Step 4: Measurement-conditioned corrections on Bob's qubit q[2]
    # (Classical feed-forward)
    # ------------------------------------------------------------------
    with qc.if_test((cr_alice[0], 1)):
        qc.x(qr[2])  # X correction if Alice's q[1] measurement = 1
    with qc.if_test((cr_alice[1], 1)):
        qc.z(qr[2])  # Z correction if Alice's q[0] measurement = 1

    qc.barrier(label="corrections")

    # ------------------------------------------------------------------
    # Step 5: Bob's verification measurement of q[2]
    # ------------------------------------------------------------------
    qc.measure(qr[2], cr_bob[0])

    return qc


def build_teleportation_circuit_statevector(theta: float, phi: float = 0.0) -> QuantumCircuit:
    """
    Builds a teleportation circuit WITHOUT the final measurement,
    suitable for statevector simulation to verify the teleported state.

    After Alice's corrections, q[2] should be in state |ψ(theta, phi)⟩.
    We verify by running the statevector simulator and checking the
    reduced density matrix or by applying the inverse rotation and
    checking collapse to |0⟩.

    Returns:
        QuantumCircuit with 3 qubits, 2 classical bits (Alice's), no Bob measurement.
    """
    qr = QuantumRegister(3, "q")
    cr_alice = ClassicalRegister(2, "alice")
    qc = QuantumCircuit(qr, cr_alice, name="teleportation_sv")

    qc.ry(theta, qr[0])
    if abs(phi) > 1e-10:
        qc.p(phi, qr[0])
    qc.barrier()

    qc.h(qr[1])
    qc.cx(qr[1], qr[2])
    qc.barrier()

    qc.cx(qr[0], qr[1])
    qc.h(qr[0])
    qc.measure(qr[1], cr_alice[0])
    qc.measure(qr[0], cr_alice[1])

    with qc.if_test((cr_alice[0], 1)):
        qc.x(qr[2])
    with qc.if_test((cr_alice[1], 1)):
        qc.z(qr[2])

    return qc


def run_teleportation(
    theta: float,
    phi: float = 0.0,
    shots: int = 1024,
    backend_id: str = "aer_simulator",
) -> dict:
    """
    Runs the teleportation circuit and returns measurement statistics.

    Args:
        theta:      Polar angle of the input state.
        phi:        Azimuthal phase angle of the input state.
        shots:      Number of simulation shots.
        backend_id: Aer backend identifier.

    Returns:
        dict with keys:
          - theta, phi: input parameters
          - counts: raw measurement counts {bitstring: count}
          - bob_0_fraction: fraction of shots where Bob measured |0⟩
          - bob_1_fraction: fraction of shots where Bob measured |1⟩
          - expected_prob_0: theoretical P(|0⟩) = cos²(θ/2)
          - expected_prob_1: theoretical P(|1⟩) = sin²(θ/2)
          - backend: backend id used
          - shots: number of shots
          - note: disclaimer string
    """
    from backend.quantum_engine.backends import get_aer_backend
    backend = get_aer_backend(backend_id)

    qc = build_teleportation_circuit(theta, phi)
    job = backend.run(qc, shots=shots)
    result = job.result()
    counts = result.get_counts()

    # Bob's bit is cr_bob[0], which is the RIGHTMOST bit in Qiskit's
    # little-endian bitstring convention: "bob alice[1] alice[0]"
    # Full bitstring format: "b a1 a0" (space between registers)
    bob_0 = 0
    bob_1 = 0
    for bitstring, count in counts.items():
        # Qiskit separates registers with spaces: "bob_bit alice_bits"
        parts = bitstring.split()
        bob_bit = parts[0]  # first register in output is bob (last added)
        if bob_bit == "0":
            bob_0 += count
        else:
            bob_1 += count

    total = bob_0 + bob_1
    expected_p0 = math.cos(theta / 2) ** 2
    expected_p1 = math.sin(theta / 2) ** 2

    return {
        "theta": theta,
        "phi": phi,
        "counts": counts,
        "bob_0_fraction": bob_0 / total if total > 0 else 0.0,
        "bob_1_fraction": bob_1 / total if total > 0 else 0.0,
        "expected_prob_0": expected_p0,
        "expected_prob_1": expected_p1,
        "backend": backend_id,
        "shots": shots,
        "note": (
            "SIMULATION via Qiskit Aer. Results are classically computed. "
            "No real quantum hardware was used."
        ),
    }
