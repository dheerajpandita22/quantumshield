"""
QuantumShield Quantum Engine — High-Level Runner

Convenience functions that combine circuit building, execution,
and result parsing into single callable units.
Used by the API layer and the quantum worker.
"""
from __future__ import annotations

import math
from typing import Optional

from backend.quantum_engine.backends import get_aer_backend
from backend.quantum_engine.bell_pair import generate_bell_pair, BellState
from backend.quantum_engine.state_preparation import prepare_ry_state
from backend.quantum_engine.teleportation import run_teleportation
from backend.quantum_engine.verification import verify_ry_state, VerificationResult
from backend.quantum_engine.measurement import MeasurementBasis, measure_state_in_basis


def run_bell_pair(
    state: BellState = BellState.PHI_PLUS,
    shots: int = 1024,
    backend_id: str = "aer_simulator",
) -> dict:
    """Generates a Bell pair and returns measurement statistics."""
    from qiskit import ClassicalRegister
    backend = get_aer_backend(backend_id)
    qc = generate_bell_pair(state)
    qc.add_register(ClassicalRegister(2, "c"))
    qc.measure([0, 1], [0, 1])
    job = backend.run(qc, shots=shots)
    result = job.result()
    counts = dict(result.get_counts())
    return {
        "bell_state": state.value,
        "counts": counts,
        "shots": shots,
        "backend": backend_id,
        "note": "SIMULATION via Qiskit Aer.",
    }


def run_ry_state_verification(
    theta: float,
    shots: int = 2048,
    tolerance: float = 0.1,
    backend_id: str = "aer_simulator",
) -> dict:
    """Runs the full RY state verification and returns a serialisable dict."""
    result: VerificationResult = verify_ry_state(theta, shots=shots, tolerance=tolerance, backend_id=backend_id)
    return {
        "theta": result.theta,
        "shots": result.shots,
        "exp_z_measured": result.exp_z_measured,
        "exp_z_theory": result.exp_z_theory,
        "exp_x_measured": result.exp_x_measured,
        "exp_x_theory": result.exp_x_theory,
        "tolerance": result.tolerance,
        "z_pass": result.z_pass,
        "x_pass": result.x_pass,
        "overall_pass": result.overall_pass,
        "note": result.note,
    }
