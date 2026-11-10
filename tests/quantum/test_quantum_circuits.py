"""
Quantum circuit tests: state preparation, Bell pairs, teleportation.
These tests run against Qiskit Aer.
"""
from __future__ import annotations

import math
import sys
import os
import pytest

# Allow running from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.quantum_engine.state_preparation import prepare_ry_state, expected_statevector
from backend.quantum_engine.bell_pair import generate_bell_pair, BellState
from backend.quantum_engine.runner import run_bell_pair, run_ry_state_verification
from backend.quantum_engine.teleportation import run_teleportation
from backend.quantum_engine.backends import get_aer_backend, list_available_backends
from backend.quantum_engine.measurement import MeasurementBasis, measure_state_in_basis
from backend.quantum_engine.verification import verify_ry_state


# ---------------------------------------------------------------------------
# Backend tests
# ---------------------------------------------------------------------------
def test_aer_backend_available():
    backend = get_aer_backend("aer_simulator")
    assert backend is not None


def test_registered_backends():
    backends = list_available_backends()
    assert len(backends) >= 1
    ids = [b.id for b in backends]
    assert "aer_simulator" in ids


def test_invalid_backend_raises():
    with pytest.raises(ValueError, match="Unknown backend"):
        get_aer_backend("does_not_exist")


# ---------------------------------------------------------------------------
# State preparation tests
# ---------------------------------------------------------------------------
def test_ry_state_circuit_has_one_qubit():
    qc = prepare_ry_state(math.pi / 2)
    assert qc.num_qubits == 1


def test_ry_state_invalid_theta_type():
    with pytest.raises(TypeError):
        prepare_ry_state("not_a_number")


def test_expected_statevector_zero():
    sv = expected_statevector(0.0)
    assert abs(sv[0] - 1.0) < 1e-10
    assert abs(sv[1] - 0.0) < 1e-10


def test_expected_statevector_pi():
    sv = expected_statevector(math.pi)
    assert abs(sv[0]) < 1e-10
    assert abs(sv[1] - 1.0) < 1e-10


def test_expected_statevector_plus():
    sv = expected_statevector(math.pi / 2)
    assert abs(abs(sv[0]) - 1 / math.sqrt(2)) < 1e-10
    assert abs(abs(sv[1]) - 1 / math.sqrt(2)) < 1e-10


# ---------------------------------------------------------------------------
# Bell pair tests
# ---------------------------------------------------------------------------
def test_bell_pair_circuit_has_two_qubits():
    qc = generate_bell_pair(BellState.PHI_PLUS)
    assert qc.num_qubits == 2


def test_bell_pair_phi_plus_counts():
    result = run_bell_pair(BellState.PHI_PLUS, shots=2048)
    counts = result["counts"]
    # |Φ+⟩ should collapse to 00 or 11 only
    for bitstring in counts:
        assert bitstring.replace(" ", "") in ("00", "11"), f"Unexpected bitstring: {bitstring}"


def test_bell_pair_psi_plus_counts():
    result = run_bell_pair(BellState.PSI_PLUS, shots=2048)
    counts = result["counts"]
    for bitstring in counts:
        assert bitstring.replace(" ", "") in ("01", "10"), f"Unexpected bitstring: {bitstring}"


# ---------------------------------------------------------------------------
# RY state verification tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("theta,name", [
    (0.0,            "|0⟩"),
    (math.pi / 2,    "|+⟩"),
    (math.pi,        "|1⟩"),
    (math.pi / 4,    "RY(π/4)"),
    (3 * math.pi / 4, "RY(3π/4)"),
])
def test_ry_verification(theta, name):
    result = verify_ry_state(theta, shots=4096, tolerance=0.1)
    assert result.overall_pass, (
        f"RY verification failed for theta={theta} ({name}): "
        f"⟨Z⟩ meas={result.exp_z_measured:.4f} theory={result.exp_z_theory:.4f}, "
        f"⟨X⟩ meas={result.exp_x_measured:.4f} theory={result.exp_x_theory:.4f}"
    )


# ---------------------------------------------------------------------------
# Teleportation tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("theta,phi,label", [
    (0.0,          0.0, "|0⟩"),
    (math.pi,      0.0, "|1⟩"),
    (math.pi / 2,  0.0, "|+⟩"),
    (math.pi / 4,  0.0, "RY(π/4)"),
    (3*math.pi/4,  0.0, "RY(3π/4)"),
])
def test_teleportation(theta, phi, label):
    result = run_teleportation(theta=theta, phi=phi, shots=4096)
    measured_p0 = result["bob_0_fraction"]
    expected_p0 = result["expected_prob_0"]
    deviation = abs(measured_p0 - expected_p0)
    tolerance = 0.05
    assert deviation <= tolerance, (
        f"Teleportation failed for state {label} (θ={theta:.4f}): "
        f"P(|0⟩) measured={measured_p0:.4f} expected={expected_p0:.4f} "
        f"deviation={deviation:.4f} > tolerance={tolerance}"
    )


def test_teleportation_counts_format():
    """Ensure run_teleportation returns the expected dict structure."""
    result = run_teleportation(theta=math.pi / 2, shots=512)
    assert "counts" in result
    assert "bob_0_fraction" in result
    assert "expected_prob_0" in result
    assert "note" in result
    assert "SIMULATION" in result["note"]
