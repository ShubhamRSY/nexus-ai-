"""Shared fixtures for end-to-end API journey tests."""

import uuid

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session_id():
    return f"e2e-{uuid.uuid4().hex[:10]}"


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    """Admin JWT for protected integrations endpoints."""
    suffix = uuid.uuid4().hex[:8]
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"e2e-admin-{suffix}@example.com",
            "password": "AdminPass123!",
            "name": "E2E Admin",
        },
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['token']}"}
