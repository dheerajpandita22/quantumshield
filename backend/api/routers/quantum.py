"""Quantum engine API endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.common.enums import ExecutionKind

router = APIRouter(prefix="/quantum", tags=["Quantum"])


class QuantumBackend(BaseModel):
    id: str
    name: str
    type: str  # "simulator" | "hardware"
    execution_kind: ExecutionKind
    available: bool
    max_qubits: int
    description: str
    note: str = ""


class QuantumJobStatus(BaseModel):
    job_id: str
    status: str
    backend: str
    created_at: str
    completed_at: Optional[str] = None
    result_summary: Optional[str] = None


class QuantumJobRequest(BaseModel):
    circuit_type: str = Field(..., description="e.g. 'bell_pair', 'teleportation', 'ry_state'")
    backend_id: str = Field(default="aer_simulator")
    shots: int = Field(default=1024, ge=1, le=100000)
    parameters: dict = Field(default_factory=dict)


_jobs: dict[str, QuantumJobStatus] = {}

AVAILABLE_BACKENDS: List[QuantumBackend] = [
    QuantumBackend(
        id="aer_simulator",
        name="Qiskit Aer Simulator",
        type="simulator",
        execution_kind=ExecutionKind.IDEAL_SIMULATOR,
        available=True,
        max_qubits=32,
        description="High-performance statevector simulator bundled with Qiskit Aer.",
        note="SIMULATION ONLY — classically computed results, not from physical quantum hardware.",
    ),
    QuantumBackend(
        id="aer_noisy_simulator",
        name="Qiskit Aer Noisy Simulator",
        type="simulator",
        execution_kind=ExecutionKind.NOISY_SIMULATOR,
        available=True,
        max_qubits=32,
        description="Noise model simulator parameterizing depolarizing and amplitude damping errors.",
        note="SIMULATION ONLY — classically computed results with simulated noise.",
    ),
    QuantumBackend(
        id="ibm_quantum_placeholder",
        name="IBM Quantum Hardware (Future)",
        type="hardware",
        execution_kind=ExecutionKind.PHYSICAL_HARDWARE,
        available=False,
        max_qubits=0,
        description="Placeholder for future physical quantum hardware via Qiskit Runtime.",
        note="NOT CONNECTED — requires external IBM Quantum credentials. Not active in MVP.",
    ),
]


@router.get("/backends", response_model=List[QuantumBackend], summary="List available quantum backends")
async def list_backends() -> List[QuantumBackend]:
    return AVAILABLE_BACKENDS


@router.post("/jobs", response_model=QuantumJobStatus, summary="Submit a quantum job")
async def submit_job(request: QuantumJobRequest) -> QuantumJobStatus:
    backend = next((b for b in AVAILABLE_BACKENDS if b.id == request.backend_id), None)
    if backend is None:
        raise HTTPException(status_code=404, detail=f"Backend '{request.backend_id}' not found.")
    if not backend.available:
        raise HTTPException(
            status_code=400,
            detail=f"Backend '{request.backend_id}' is not available. {backend.note}",
        )

    job_id = str(uuid4())
    job = QuantumJobStatus(
        job_id=job_id,
        status="QUEUED",
        backend=request.backend_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        result_summary="Job queued in local registry.",
    )
    _jobs[job_id] = job
    return job


@router.get("/jobs", response_model=List[QuantumJobStatus], summary="List jobs")
async def list_jobs() -> List[QuantumJobStatus]:
    return list(_jobs.values())


@router.get("/jobs/{job_id}", response_model=QuantumJobStatus, summary="Get job details")
async def get_job(job_id: str) -> QuantumJobStatus:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job
