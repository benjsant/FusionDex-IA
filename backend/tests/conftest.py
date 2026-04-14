"""Shared pytest fixtures.

Tests run against the live dev Postgres (data loaded by the ETL pipeline).
They assume the database is populated with the canonical 572 Pokémon dataset.

Run from the repo root:
    POSTGRES_PASSWORD=... uv run --project backend pytest backend/tests/

POSTGRES_HOST defaults to 'localhost' (docker exposes 5432).
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("POSTGRES_HOST", "localhost")

from backend.main import app  # noqa: E402  (env must be set before import)


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
