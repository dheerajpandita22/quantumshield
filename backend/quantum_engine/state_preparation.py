"""
QuantumShield Quantum Engine — State Preparation

Implements qubit state preparation circuits using parameterized RY rotations
and optional phase shifts. These circuits prepare the quantum state that will
be teleported or used in protocol demonstrations.

Circuit convention: qubit 0 is the data qubit to prepare.
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import Parameter


def prepare_ry_state(theta: float, label: str = "state_prep") -> QuantumCircuit:
    """
    Prepares the single-qubit state: |ψ⟩ = cos(θ/2)|0⟩ + sin(θ/2)|1⟩

    This is a pure real-amplitude state on the XZ plane of the Bloch sphere.
    The global phase is irrelevant and is not set here.

    Args:
        theta: Rotation angle in radians. Special values:
               0        → |0⟩
               π/2      → (|0⟩ + |1⟩) / √2  (|+⟩)
               π        → |1⟩
               3π/4     → cos(3π/8)|0⟩ + sin(3π/8)|1⟩
        label: Optional circuit label for display purposes.

    Returns:
        A QuantumCircuit acting on 1 qubit that prepares |ψ(θ)⟩.
    """
    if not isinstance(theta, (int, float)):
        raise TypeError(f"theta must be a real number, got {type(theta)}")

    qr = QuantumRegister(1, "q")
    qc = QuantumCircuit(qr, name=label)
    qc.ry(theta, qr[0])
    return qc


def prepare_ry_phase_state(theta: float, phi: float, label: str = "state_prep_phase") -> QuantumCircuit:
    """
    Prepares the general single-qubit state with phase:
    |ψ⟩ = cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩

    Args:
        theta: Polar angle in radians (Bloch sphere latitude).
        phi:   Azimuthal angle in radians (Bloch sphere longitude).
        label: Optional circuit label.

    Returns:
        A QuantumCircuit preparing the specified state on 1 qubit.
    """
    if not isinstance(theta, (int, float)):
        raise TypeError(f"theta must be a real number, got {type(theta)}")
    if not isinstance(phi, (int, float)):
        raise TypeError(f"phi must be a real number, got {type(phi)}")

    qr = QuantumRegister(1, "q")
    qc = QuantumCircuit(qr, name=label)
    # U gate: U(θ, φ, λ) = Rz(φ+λ) Ry(θ)
    # For |ψ⟩ = cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩ use U(theta, phi, 0)
    qc.u(theta, phi, 0.0, qr[0])
    return qc


def expected_statevector(theta: float, phi: float = 0.0) -> np.ndarray:
    """
    Returns the expected numpy statevector for the state prepared by
    prepare_ry_phase_state(theta, phi).

    Returns:
        np.ndarray of shape (2,) with dtype complex128.
    """
    alpha = math.cos(theta / 2)
    beta = math.sin(theta / 2) * np.exp(1j * phi)
    return np.array([alpha, beta], dtype=complex)
