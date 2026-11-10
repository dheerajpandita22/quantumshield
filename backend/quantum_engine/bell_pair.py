"""
QuantumShield Quantum Engine — Bell Pair Generation

Generates the four Bell states (maximally entangled two-qubit states).
Bell pairs are the fundamental resource for quantum teleportation.

Qubit convention:
  q[0] = Alice's qubit (sent to sender / source of entanglement)
  q[1] = Bob's qubit   (sent to receiver)

Bell basis:
  |Φ+⟩ = (|00⟩ + |11⟩) / √2   ← default
  |Φ-⟩ = (|00⟩ - |11⟩) / √2
  |Ψ+⟩ = (|01⟩ + |10⟩) / √2
  |Ψ-⟩ = (|01⟩ - |10⟩) / √2
"""
from __future__ import annotations

from enum import Enum

from qiskit import QuantumCircuit, QuantumRegister


class BellState(str, Enum):
    PHI_PLUS = "phi_plus"    # |Φ+⟩  default
    PHI_MINUS = "phi_minus"  # |Φ-⟩
    PSI_PLUS = "psi_plus"    # |Ψ+⟩
    PSI_MINUS = "psi_minus"  # |Ψ-⟩


def generate_bell_pair(state: BellState = BellState.PHI_PLUS) -> QuantumCircuit:
    """
    Returns a 2-qubit QuantumCircuit that generates the specified Bell state.

    The circuit starts from |00⟩ and uses H + CNOT (plus optional X/Z)
    to reach the target Bell state.

    Args:
        state: Which of the four Bell states to prepare.

    Returns:
        QuantumCircuit on 2 qubits.
    """
    qr = QuantumRegister(2, "bell")
    qc = QuantumCircuit(qr, name=f"bell_{state.value}")

    # Base: |Φ+⟩ = H on q0, then CNOT(q0 → q1)
    qc.h(qr[0])
    qc.cx(qr[0], qr[1])

    if state == BellState.PHI_MINUS:
        qc.z(qr[0])
    elif state == BellState.PSI_PLUS:
        qc.x(qr[1])
    elif state == BellState.PSI_MINUS:
        qc.x(qr[1])
        qc.z(qr[0])
    # PHI_PLUS: no additional gates

    return qc


def bell_basis_measurement(qc: QuantumCircuit, q0: int, q1: int) -> QuantumCircuit:
    """
    Appends a Bell-basis measurement block to an existing circuit.
    Used in the sender half of quantum teleportation.

    The Bell-basis measurement consists of:
      1. CNOT(q0 → q1)   — entangling in the Bell basis
      2. H(q0)           — Hadamard to convert X-basis → Z-basis
      3. Measure q0, q1  (must already have classical bits in `qc`)

    Args:
        qc: The QuantumCircuit to append to (must have classical registers).
        q0: Index of the first qubit to measure.
        q1: Index of the second qubit to measure.

    Returns:
        The modified QuantumCircuit (in-place, also returned for chaining).
    """
    qc.cx(q0, q1)
    qc.h(q0)
    return qc
