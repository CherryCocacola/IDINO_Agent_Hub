"""Tests for the health check endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_check_returns_200(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check_response_format(client):
    resp = await client.get("/health")
    data = resp.json()
    assert isinstance(data, dict)
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
