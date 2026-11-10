"""
QuantumShield Quantum Engine — Measurement Utilities

Provides helper circuits and functions for measuring qubits in the
X, Y, and Z bases, and for extracting statistics from simulation results.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict

import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister


class MeasurementBasis(str, Enum):
    Z = "Z"  # Computational basis (default)
    X = "X"  # Hadamard basis
    Y = "Y"  # Y basis


def add_measurement(
    qc: QuantumCircuit,
    qubit_index: int,
    basis: MeasurementBasis = MeasurementBasis.Z,
    cbit_index: int = 0,
) -> QuantumCircuit:
    """
    Appends a single-qubit measurement in the specified basis to `qc`.

    For X-basis: apply H before measuring.
    For Y-basis: apply Sdg then H before measuring.
    For Z-basis: measure directly.

    The circuit must already have a ClassicalRegister attached.

    Args:
        qc:          Circuit to modify (in-place).
        qubit_index: Index of the qubit to measure.
        basis:       Measurement basis.
        cbit_index:  Index of the classical bit to store the result.

    Returns:
        Modified QuantumCircuit.
    """
    if basis == MeasurementBasis.X:
        qc.h(qubit_index)
    elif basis == MeasurementBasis.Y:
        qc.sdg(qubit_index)
        qc.h(qubit_index)
    # Z: no rotation needed
    qc.measure(qubit_index, cbit_index)
    return qc


def measure_state_in_basis(
    prep_circuit: QuantumCircuit,
    basis: MeasurementBasis,
    shots: int = 1024,
    backend_id: str = "aer_simulator",
) -> Dict[str, int]:
    """
    Takes a state-preparation circuit (no measurement), appends a
    measurement in the requested basis, runs it, and returns counts.

    Args:
        prep_circuit: Circuit that prepares the state on qubit 0.
        basis:        Basis to measure in.
        shots:        Number of shots.
        backend_id:   Aer backend identifier.

    Returns:
        Dict mapping bitstring → count.
    """
    from backend.quantum_engine.backends import get_aer_backend
    backend = get_aer_backend(backend_id)

    qc = prep_circuit.copy()
    qc.add_register(ClassicalRegister(1, "meas"))
    add_measurement(qc, qubit_index=0, basis=basis, cbit_index=0)

    job = backend.run(qc, shots=shots)
    result = job.result()
    return dict(result.get_counts())


def expectation_value_z(counts: Dict[str, int]) -> float:
    """
    Computes <Z> from a Z-basis measurement count dictionary.
    <Z> = (N_0 - N_1) / (N_0 + N_1)
    """
    n0 = sum(v for k, v in counts.items() if k.strip().endswith("0"))
    n1 = sum(v for k, v in counts.items() if k.strip().endswith("1"))
    total = n0 + n1
    return (n0 - n1) / total if total > 0 else 0.0
