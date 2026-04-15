"""Tests for /ai route."""

from fastapi.testclient import TestClient


def test_ai_missing_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    r = client.post("/ai/ask", json={"message": "salut"})
    assert r.status_code == 503
    assert "DEEPSEEK_API_KEY" in r.json()["detail"]
