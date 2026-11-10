"""
QuantumShield Quantum Engine — Noise Model Utilities

Provides factory functions for constructing Qiskit Aer noise models
for realistic simulation of near-term quantum hardware imperfections.

Usage:
  - ideal_noise_model()         → no errors (default)
  - depolarizing_noise_model()  → symmetric depolarizing channel
  - amplitude_damping_model()   → T1 relaxation model

IMPORTANT: These are SIMULATED noise models, not measurements from
real hardware. They parameterise known error types for analysis.
"""
from __future__ import annotations

from typing import Optional

from qiskit_aer.noise import NoiseModel, depolarizing_error, amplitude_damping_error, phase_damping_error


def ideal_noise_model() -> None:
    """Returns None to indicate no noise model (ideal simulation)."""
    return None


def depolarizing_noise_model(
    single_qubit_error: float = 0.001,
    two_qubit_error: float = 0.01,
) -> NoiseModel:
    """
    Constructs a depolarizing noise model.

    Args:
        single_qubit_error: Depolarizing error probability for 1-qubit gates.
        two_qubit_error:    Depolarizing error probability for 2-qubit gates.

    Returns:
        Qiskit Aer NoiseModel.
    """
    if not (0.0 <= single_qubit_error <= 1.0):
        raise ValueError(f"single_qubit_error must be in [0, 1], got {single_qubit_error}")
    if not (0.0 <= two_qubit_error <= 1.0):
        raise ValueError(f"two_qubit_error must be in [0, 1], got {two_qubit_error}")

    nm = NoiseModel()
    err1 = depolarizing_error(single_qubit_error, 1)
    err2 = depolarizing_error(two_qubit_error, 2)
    nm.add_all_qubit_quantum_error(err1, ["h", "ry", "rz", "u", "p", "x", "z", "s", "sdg"])
    nm.add_all_qubit_quantum_error(err2, ["cx"])
    return nm


def amplitude_damping_noise_model(gamma: float = 0.01) -> NoiseModel:
    """
    Constructs an amplitude-damping noise model (T1 relaxation).

    Args:
        gamma: Damping parameter ∈ [0, 1]. Probability of |1⟩ → |0⟩ decay.

    Returns:
        Qiskit Aer NoiseModel.
    """
    if not (0.0 <= gamma <= 1.0):
        raise ValueError(f"gamma must be in [0, 1], got {gamma}")

    nm = NoiseModel()
    err = amplitude_damping_error(gamma)
    nm.add_all_qubit_quantum_error(err, ["h", "ry", "rz", "u", "p", "x", "z"])
    return nm
