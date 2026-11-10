"""
QuantumShield Quantum Engine — Backend Abstraction Layer

Provides a unified interface for selecting and accessing quantum backends.
Currently supports Qiskit Aer simulation backends.
Future: IBM Quantum Runtime, IonQ, Rigetti (when credentials provided).

IMPORTANT: All execution on Day 1 is SIMULATION via Qiskit Aer.
No real quantum hardware is accessed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from qiskit_aer import AerSimulator


class BackendType(str, Enum):
    SIMULATOR = "simulator"
    HARDWARE = "hardware"


@dataclass
class BackendInfo:
    id: str
    name: str
    backend_type: BackendType
    max_qubits: int
    description: str
    available: bool = True
    note: str = ""


REGISTERED_BACKENDS: dict[str, BackendInfo] = {
    "aer_simulator": BackendInfo(
        id="aer_simulator",
        name="Qiskit Aer Simulator (statevector/noise)",
        backend_type=BackendType.SIMULATOR,
        max_qubits=32,
        description="General-purpose Aer simulator supporting statevector, density matrix, and noise models.",
        note="SIMULATION ONLY — classically computed results.",
    ),
    "statevector_simulator": BackendInfo(
        id="statevector_simulator",
        name="Statevector Simulator",
        backend_type=BackendType.SIMULATOR,
        max_qubits=32,
        description="Exact statevector simulator for noiseless analysis.",
        note="SIMULATION ONLY — classically computed results.",
    ),
}


def get_aer_backend(backend_id: str = "aer_simulator") -> AerSimulator:
    """
    Returns an AerSimulator instance for the requested backend ID.
    Raises ValueError for unknown or unavailable backends.
    """
    if backend_id not in REGISTERED_BACKENDS:
        raise ValueError(f"Unknown backend '{backend_id}'. Registered: {list(REGISTERED_BACKENDS.keys())}")

    info = REGISTERED_BACKENDS[backend_id]
    if not info.available:
        raise RuntimeError(f"Backend '{backend_id}' is not currently available. {info.note}")

    if backend_id == "statevector_simulator":
        return AerSimulator(method="statevector")

    return AerSimulator()


def list_available_backends() -> list[BackendInfo]:
    """Returns all registered backends (available and unavailable)."""
    return list(REGISTERED_BACKENDS.values())
