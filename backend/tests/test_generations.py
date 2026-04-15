"""Tests for /generations routes."""

from fastapi.testclient import TestClient


def test_list_generations(client: TestClient) -> None:
    r = client.get("/generations/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 7  # at least gens 1..7
    first = data[0]
    assert set(first.keys()) == {"id", "name_en", "name_fr"}


def test_generation_detail(client: TestClient) -> None:
    r = client.get("/generations/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_generation_not_found(client: TestClient) -> None:
    assert client.get("/generations/999").status_code == 404


def test_generation_pokemon(client: TestClient) -> None:
    r = client.get("/generations/1/pokemon")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 100  # gen 1 = 151+ Pokémon
    ids = {p["id"] for p in data}
    assert 1 in ids  # Bulbasaur
