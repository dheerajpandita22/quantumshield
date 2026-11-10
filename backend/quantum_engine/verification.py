"""
QuantumShield Quantum Engine — State Verification

Verifies that a teleportation (or other quantum protocol) has successfully
reproduced the intended target state within a statistical tolerance.

Verification strategy:
  1. Run the full teleportation circuit N times (shots).
  2. Measure Bob's qubit in Z, X, and Y bases.
  3. Compare estimated expectation values against the theoretical values
     for the input state |ψ(θ, φ)⟩.
  4. Report pass/fail with actual vs expected values.

This is a statistical test valid for simulation. Physical hardware
would additionally require error-mitigation and calibration.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister

from backend.quantum_engine.measurement import MeasurementBasis, measure_state_in_basis, expectation_value_z
from backend.quantum_engine.state_preparation import prepare_ry_state


@dataclass
class VerificationResult:
    theta: float
    phi: float
    shots: int
    # Measured expectation values
    exp_z_measured: float
    exp_x_measured: float
    # Theoretical expectation values
    exp_z_theory: float
    exp_x_theory: float
    # Tolerance
    tolerance: float
    # Pass/fail
    z_pass: bool
    x_pass: bool
    overall_pass: bool
    # Raw counts
    z_counts: dict = field(default_factory=dict)
    x_counts: dict = field(default_factory=dict)
    note: str = ""


def theoretical_expectations(theta: float, phi: float = 0.0) -> dict:
    """
    Returns theoretical ⟨X⟩, ⟨Y⟩, ⟨Z⟩ for state cos(θ/2)|0⟩ + e^{iφ}sin(θ/2)|1⟩.

    Bloch vector: (sin θ cos φ, sin θ sin φ, cos θ)
    """
    return {
        "exp_x": math.sin(theta) * math.cos(phi),
        "exp_y": math.sin(theta) * math.sin(phi),
        "exp_z": math.cos(theta),
    }


def verify_ry_state(
    theta: float,
    phi: float = 0.0,
    shots: int = 2048,
    tolerance: float = 0.1,
    backend_id: str = "aer_simulator",
) -> VerificationResult:
    """
    Verifies that prepare_ry_state(theta) produces the correct state by
    measuring in Z and X bases and comparing to theoretical expectations.

    Args:
        theta:      Rotation angle (radians).
        phi:        Phase angle (radians). Currently only Z and X are checked
                    for real states; phi is recorded for completeness.
        shots:      Simulation shots per basis.
        tolerance:  Allowed absolute deviation |measured - theoretical|.
        backend_id: Aer backend.

    Returns:
        VerificationResult dataclass.
    """
    theory = theoretical_expectations(theta, phi)

    prep = prepare_ry_state(theta)
    z_counts = measure_state_in_basis(prep, MeasurementBasis.Z, shots, backend_id)
    x_counts = measure_state_in_basis(prep, MeasurementBasis.X, shots, backend_id)

    exp_z = expectation_value_z(z_counts)
    exp_x = expectation_value_z(x_counts)

    z_pass = abs(exp_z - theory["exp_z"]) <= tolerance
    x_pass = abs(exp_x - theory["exp_x"]) <= tolerance

    return VerificationResult(
        theta=theta,
        phi=phi,
        shots=shots,
        exp_z_measured=exp_z,
        exp_x_measured=exp_x,
        exp_z_theory=theory["exp_z"],
        exp_x_theory=theory["exp_x"],
        tolerance=tolerance,
        z_pass=z_pass,
        x_pass=x_pass,
        overall_pass=z_pass and x_pass,
        z_counts=z_counts,
        x_counts=x_counts,
        note="SIMULATION via Qiskit Aer. Statistical verification only.",
    )
