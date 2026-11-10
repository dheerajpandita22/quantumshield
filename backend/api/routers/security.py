"""Security events API endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/security", tags=["Security"])


class SecurityEvent(BaseModel):
    event_id: str
    event_type: str
    severity: str
    source: str
    description: str
    timestamp: str
    resolved: bool = False
    metadata: dict = {}


_SEED_EVENTS: List[SecurityEvent] = [
    SecurityEvent(
        event_id=str(uuid4()),
        event_type="system.started",
        severity="INFO",
        source="api",
        description="QuantumShield API online. Health checks and security middleware operational.",
        timestamp=datetime.now(timezone.utc).isoformat(),
        resolved=True,
        metadata={"note": "System bootstrap event marker."},
    ),
]


@router.get("/events", response_model=List[SecurityEvent], summary="List security events")
async def list_events(
    severity: Optional[str] = Query(default=None),
    resolved: Optional[bool] = Query(default=None),
) -> List[SecurityEvent]:
    events = list(_SEED_EVENTS)
    if severity:
        events = [e for e in events if e.severity == severity.upper()]
    if resolved is not None:
        events = [e for e in events if e.resolved == resolved]
    return events
