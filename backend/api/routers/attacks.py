"""Attack simulation API endpoints."""
from __future__ import annotations

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/attack", tags=["Attack Simulation"])


class AttackScenario(BaseModel):
    id: str
    name: str
    category: str
    description: str
    risk_level: str
    status: str
    note: str = ""


SCENARIOS: List[AttackScenario] = [
    AttackScenario(
        id="sig_forgery_v1",
        name="Quantum Signature Forgery",
        category="Forgery",
        description="Simulates adversary attempting to forge quantum signature without original state.",
        risk_level="HIGH",
        status="PLANNED",
        note="UNIMPLEMENTED STUB — Authorized sandbox target only.",
    ),
    AttackScenario(
        id="impersonation_v1",
        name="Quantum-Channel Impersonation",
        category="Impersonation",
        description="Simulates adversary impersonating trusted party over quantum channel.",
        risk_level="HIGH",
        status="PLANNED",
        note="UNIMPLEMENTED STUB — Authorized sandbox target only.",
    ),
    AttackScenario(
        id="replay_v1",
        name="Replay Attack",
        category="Replay",
        description="Simulates message replay bypassing freshness and nonces.",
        risk_level="MEDIUM",
        status="PLANNED",
        note="UNIMPLEMENTED STUB — Authorized sandbox target only.",
    ),
    AttackScenario(
        id="channel_manip_v1",
        name="Quantum-Channel Manipulation",
        category="Channel Manipulation",
        description="Simulates intercept-and-resend or channel tampering in quantum transmission.",
        risk_level="HIGH",
        status="PLANNED",
        note="UNIMPLEMENTED STUB — Authorized sandbox target only.",
    ),
]


@router.get("/scenarios", response_model=List[AttackScenario], summary="List attack scenarios")
async def list_scenarios() -> List[AttackScenario]:
    """
    Returns defined attack scenarios.
    IMPORTANT: All scenarios run strictly in isolated local sandboxes.
    """
    return SCENARIOS
