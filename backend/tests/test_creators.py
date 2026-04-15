"""Tests for /creators routes."""

from fastapi.testclient import TestClient


def test_list_creators(client: TestClient) -> None:
    r = client.get("/creators/?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 5
    # Ordered by sprite_count desc
    counts = [c["sprite_count"] for c in data]
    assert counts == sorted(counts, reverse=True)


def test_creator_filter_by_name(client: TestClient) -> None:
    r = client.get("/creators/?q=a&limit=3")
    assert r.status_code == 200
    for c in r.json():
        assert "a" in c["name"].lower()


def test_creator_detail_and_sprites(client: TestClient) -> None:
    # Grab first creator from list
    top = client.get("/creators/?limit=1").json()[0]
    cid = top["id"]
    r = client.get(f"/creators/{cid}")
    assert r.status_code == 200
    assert r.json()["id"] == cid

    r = client.get(f"/creators/{cid}/sprites")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_creator_not_found(client: TestClient) -> None:
    assert client.get("/creators/9999999").status_code == 404
    assert client.get("/creators/9999999/sprites").status_code == 404
