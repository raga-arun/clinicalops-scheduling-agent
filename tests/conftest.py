"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def tenant_headers() -> dict[str, str]:
    return {"X-Tenant-ID": "tenant-test"}
