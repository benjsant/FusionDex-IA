"""Tests for /moves and /types routes."""

from fastapi.testclient import TestClient


def test_list_moves(client: TestClient) -> None:
    r = client.get("/moves/?limit=5")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_filter_category(client: TestClient) -> None:
    r = client.get("/moves/?category=Status&limit=100")
    assert r.status_code == 200
    assert all(m["category"] == "Status" for m in r.json())


def test_filter_power_min(client: TestClient) -> None:
    r = client.get("/moves/?power_min=100&limit=20")
    assert r.status_code == 200
    assert all((m["power"] or 0) >= 100 for m in r.json())


def test_filter_power_range(client: TestClient) -> None:
    r = client.get("/moves/?power_min=60&power_max=80")
    assert r.status_code == 200
    for m in r.json():
        assert 60 <= (m["power"] or 0) <= 80


def test_filter_type_id(client: TestClient) -> None:
    # type_id 7 = Fire
    r = client.get("/moves/?type_id=7&limit=10")
    assert r.status_code == 200
    assert all(m["type"]["name_en"] == "Fire" for m in r.json())


def test_search_move(client: TestClient) -> None:
    r = client.get("/moves/search?q=flamm")
    assert r.status_code == 200
    names = {m["name_fr"] for m in r.json()}
    assert any("Flamm" in n for n in names if n)


def test_by_type_fr(client: TestClient) -> None:
    r = client.get("/moves/by-type/Feu")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_move_detail_404(client: TestClient) -> None:
    r = client.get("/moves/999999")
    assert r.status_code == 404


def test_move_invalid_category(client: TestClient) -> None:
    r = client.get("/moves/?category=Bogus")
    assert r.status_code == 422


def test_types_list(client: TestClient) -> None:
    r = client.get("/types/")
    assert r.status_code == 200
    assert len(r.json()) >= 18  # 18 canonical + triple-fusion types


def test_types_by_name_fr(client: TestClient) -> None:
    r = client.get("/types/by-name/Feu")
    assert r.status_code == 200
    assert r.json()["name_en"] == "Fire"


def test_abilities_list(client: TestClient) -> None:
    r = client.get("/abilities/")
    assert r.status_code == 200
    assert len(r.json()) > 100


def test_ability_search(client: TestClient) -> None:
    r = client.get("/abilities/search?q=blaze")
    assert r.status_code == 200
    assert any(a["name_en"] == "Blaze" for a in r.json())
