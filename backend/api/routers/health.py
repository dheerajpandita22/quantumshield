"""Health check endpoints."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import get_settings

router = APIRouter(tags=["Health"])
_start_time = time.time()
settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime_seconds: float
    timestamp: str


@router.get("/health", response_model=HealthResponse, summary="Root health check")
async def root_health() -> HealthResponse:
    """Basic liveness probe."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=round(time.time() - _start_time, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/api/v1/health", response_model=HealthResponse, summary="Versioned health check")
async def v1_health() -> HealthResponse:
    """Versioned liveness probe for load-balancer integration."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=round(time.time() - _start_time, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
