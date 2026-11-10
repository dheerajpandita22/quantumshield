"""Unit tests for health endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from backend.api.main import app


@pytest.mark.asyncio
async def test_root_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_v1_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_quantum_backends():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/quantum/backends")
    assert response.status_code == 200
    backends = response.json()
    assert isinstance(backends, list)
    assert len(backends) >= 1
    ids = [b["id"] for b in backends]
    assert "aer_simulator" in ids


@pytest.mark.asyncio
async def test_attack_scenarios():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/attack/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 1


@pytest.mark.asyncio
async def test_security_events():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/security/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)


@pytest.mark.asyncio
async def test_job_invalid_backend():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/quantum/jobs",
            json={"circuit_type": "bell_pair", "backend_id": "nonexistent_backend", "shots": 100},
        )
    assert response.status_code == 404
