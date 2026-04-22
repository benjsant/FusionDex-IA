"""Tests for /items route."""

from fastapi.testclient import TestClient


def test_list_items(client: TestClient) -> None:
    r = client.get("/items/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 70  # 6 fusion + 24 evolution + 40 valuables


def test_filter_category_fusion(client: TestClient) -> None:
    r = client.get("/items/?category=fusion")
    assert r.status_code == 200
    items = r.json()
    assert all(i["category"] == "fusion" for i in items)
    assert any(i["name_en"] == "DNA Splicers" for i in items)


def test_filter_category_valuable(client: TestClient) -> None:
    r = client.get("/items/?category=valuable")
    assert r.status_code == 200
    items = r.json()
    heart = next((i for i in items if i["name_en"] == "Heart Scale"), None)
    assert heart is not None
    assert heart["price_sell"] == 50


def test_search_fire_stone(client: TestClient) -> None:
    r = client.get("/items/search?q=Fire Stone")
    assert r.status_code == 200
    items = r.json()
    assert any(i["name_en"] == "Fire Stone" and i["price_buy"] == 5000 for i in items)


def test_item_detail_404(client: TestClient) -> None:
    r = client.get("/items/999999")
    assert r.status_code == 404


def test_invalid_category(client: TestClient) -> None:
    r = client.get("/items/?category=bogus")
    assert r.status_code == 422
