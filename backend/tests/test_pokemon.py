"""Tests for /pokemon routes."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_list_pagination(client: TestClient) -> None:
    r = client.get("/pokemon/?limit=3")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 3
    assert [p["id"] for p in items] == [1, 2, 3]
    assert items[0]["name_en"] == "Bulbasaur"


def test_list_offset(client: TestClient) -> None:
    r = client.get("/pokemon/?offset=500&limit=5")
    assert r.status_code == 200
    assert [p["id"] for p in r.json()] == [501, 502, 503, 504, 505]


def test_filter_by_type(client: TestClient) -> None:
    # type_id 7 = Fire — Charmander is one of them
    r = client.get("/pokemon/?type_id=7")
    assert r.status_code == 200
    names = {p["name_en"] for p in r.json()}
    assert "Charmander" in names
    assert "Charizard" in names
    assert "Bulbasaur" not in names


def test_filter_by_generation(client: TestClient) -> None:
    r = client.get("/pokemon/?generation_id=1")
    assert r.status_code == 200
    assert len(r.json()) == 151


def test_filter_include_hoenn_false(client: TestClient) -> None:
    all_count = len(client.get("/pokemon/").json())
    no_hoenn = len(client.get("/pokemon/?include_hoenn=false").json())
    assert no_hoenn < all_count


def test_detail_charizard(client: TestClient) -> None:
    r = client.get("/pokemon/6")
    assert r.status_code == 200
    p = r.json()
    assert p["name_en"] == "Charizard"
    assert p["name_fr"] == "Dracaufeu"
    types = {t["name_en"] for t in p["types"]}
    assert types == {"Fire", "Flying"}
    assert any(a["name_en"] == "Blaze" for a in p["abilities"])


def test_detail_not_found(client: TestClient) -> None:
    r = client.get("/pokemon/9999")
    assert r.status_code == 404
    assert "9999" in r.json()["detail"]


def test_search_accent_insensitive(client: TestClient) -> None:
    r = client.get("/pokemon/search?q=draca")
    assert r.status_code == 200
    names = [p["name_fr"] for p in r.json()]
    assert "Dracaufeu" in names


def test_moves_endpoint(client: TestClient) -> None:
    r = client.get("/pokemon/6/moves")
    assert r.status_code == 200
    moves = r.json()
    assert len(moves) > 0
    methods = {m["method"] for m in moves}
    assert methods & {"level_up", "tm"}


def test_evolutions_endpoint(client: TestClient) -> None:
    # Charmander -> Charmeleon
    r = client.get("/pokemon/4/evolutions")
    assert r.status_code == 200
    data = r.json()
    assert any(e["evolves_into_name_en"] == "Charmeleon" for e in data)


def test_weaknesses_endpoint(client: TestClient) -> None:
    # Charizard: weak to Rock (4x), Electric (2x), Water (2x)
    r = client.get("/pokemon/6/weaknesses")
    assert r.status_code == 200
    data = r.json()
    rock = next((w for w in data if w["attacking_type_name_en"] == "Rock"), None)
    assert rock is not None
    assert float(rock["multiplier"]) == 4.0


def test_locations_endpoint_structure(client: TestClient) -> None:
    r = client.get("/pokemon/1/locations")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
