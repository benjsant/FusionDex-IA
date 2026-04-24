"""Unit tests for the AI tool handlers (backend.services.ai_tools).

Each tool is tested in isolation with a real DB session (via the `db`
fixture from conftest.py). No DeepSeek involvement here — the LLM loop
is tested separately.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from backend.db.session import SessionLocal
from backend.services.ai_tools import (
    TOOL_HANDLERS,
    TOOL_SPECS,
    dispatch_tool,
)


@pytest.fixture
def db() -> Iterator[Session]:
    """Yield a real DB session (these tests require the populated dev DB)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ─── Spec consistency ────────────────────────────────────────────────────────

def test_tool_specs_match_handlers() -> None:
    """Every declared tool has a handler and vice-versa."""
    spec_names = {s["function"]["name"] for s in TOOL_SPECS}
    handler_names = set(TOOL_HANDLERS.keys())
    assert spec_names == handler_names, (
        f"Spec/handler mismatch. In specs but not handlers: "
        f"{spec_names - handler_names}. In handlers but not specs: "
        f"{handler_names - spec_names}."
    )


def test_tool_specs_are_valid_openai_schema() -> None:
    """Each spec follows the OpenAI function-calling structure."""
    for spec in TOOL_SPECS:
        assert spec["type"] == "function"
        fn = spec["function"]
        assert "name" in fn and isinstance(fn["name"], str)
        assert "description" in fn and isinstance(fn["description"], str)
        assert "parameters" in fn
        params = fn["parameters"]
        assert params["type"] == "object"
        assert "properties" in params and isinstance(params["properties"], dict)
        # required is optional in OpenAI spec but we always declare it
        assert isinstance(params.get("required", []), list)


# ─── get_pokemon ─────────────────────────────────────────────────────────────

def test_get_pokemon_by_id(db) -> None:
    result = dispatch_tool(db, "get_pokemon", {"name_or_id": 25})
    assert result["id"] == 25
    assert result["name_en"] == "Pikachu"
    assert "Electric" in result["types"]
    assert result["stats"]["speed"] == 90


def test_get_pokemon_by_name(db) -> None:
    result = dispatch_tool(db, "get_pokemon", {"name_or_id": "Charizard"})
    assert result["name_en"] == "Charizard"
    assert set(result["types"]) >= {"Fire"}


def test_get_pokemon_not_found(db) -> None:
    result = dispatch_tool(db, "get_pokemon", {"name_or_id": 999999})
    assert "error" in result


def test_get_pokemon_missing_arg(db) -> None:
    result = dispatch_tool(db, "get_pokemon", {})
    assert "error" in result


# ─── get_fusion ──────────────────────────────────────────────────────────────

def test_get_fusion_pikachu_charizard(db) -> None:
    result = dispatch_tool(db, "get_fusion", {"head": 25, "body": 6})
    assert result["head"]["name_en"] == "Pikachu"
    assert result["body"]["name_en"] == "Charizard"
    assert "Electric" in result["types"]
    # Fusion stats are deterministic
    assert result["stats"]["hp"] > 0
    assert isinstance(result["expert_moves"], list)


def test_get_fusion_heart_scale_prices_exposed(db) -> None:
    """Expert moves carry per-location Heart Scale prices."""
    result = dispatch_tool(db, "get_fusion", {"head": "Umbreon", "body": "Bulbasaur"})
    assert result.get("expert_moves")
    for m in result["expert_moves"]:
        assert m["prices_heart_scales"]
        for loc, price in m["prices_heart_scales"].items():
            assert price == (2 if loc == "knot_island" else 10)


def test_get_fusion_invalid_head(db) -> None:
    result = dispatch_tool(db, "get_fusion", {"head": 999999, "body": 1})
    assert "error" in result
    assert "head" in result["error"]


# ─── search_move ─────────────────────────────────────────────────────────────

def test_search_move_with_tm_info(db) -> None:
    """TM05 = Roar, taught at Celadon + Route 32."""
    result = dispatch_tool(db, "search_move", {"name": "Roar"})
    assert result["name_en"] == "Roar"
    assert result["tm"] is not None
    assert result["tm"]["number"] == 5
    loc_names = {l["name_en"] for l in result["tm"]["locations"]}
    assert "Celadon City" in loc_names


def test_search_move_with_tutors(db) -> None:
    """Bug Bite is taught by a tutor on Route 2 (₽2000)."""
    result = dispatch_tool(db, "search_move", {"name": "Bug Bite"})
    assert result["tutors"]
    assert any(
        t["location"] == "Route 2" and t["price"] == 2000
        for t in result["tutors"]
    )


def test_search_move_not_found(db) -> None:
    result = dispatch_tool(db, "search_move", {"name": "NotARealMoveXYZ"})
    assert "error" in result


# ─── get_item ────────────────────────────────────────────────────────────────

def test_get_item_heart_scale(db) -> None:
    result = dispatch_tool(db, "get_item", {"name": "Heart Scale"})
    assert result["name_en"] == "Heart Scale"
    assert result["category"] == "valuable"
    assert result["price_buy"] == 5000
    assert result["price_sell"] == 50


def test_get_item_fire_stone(db) -> None:
    result = dispatch_tool(db, "get_item", {"name": "Fire Stone"})
    assert result["category"] == "evolution"
    assert result["price_buy"] == 5000


def test_get_item_not_found(db) -> None:
    result = dispatch_tool(db, "get_item", {"name": "NotARealItem"})
    assert "error" in result


# ─── get_move_tutors ─────────────────────────────────────────────────────────

def test_get_move_tutors_bug_bite(db) -> None:
    result = dispatch_tool(db, "get_move_tutors", {"move_name": "Bug Bite"})
    assert result["move"]["name_en"] == "Bug Bite"
    assert len(result["tutors"]) == 1
    t = result["tutors"][0]
    assert t["location"] == "Route 2"
    assert t["currency"] == "pokedollars"
    assert t["price"] == 2000


def test_get_move_tutors_empty(db) -> None:
    """Most moves have no classical tutor — empty list, not 404."""
    result = dispatch_tool(db, "get_move_tutors", {"move_name": "Pound"})
    assert "move" in result
    assert result["tutors"] == []


# ─── dispatch_tool safety ────────────────────────────────────────────────────

def test_dispatch_unknown_tool(db) -> None:
    result = dispatch_tool(db, "nonexistent_tool", {})
    assert "error" in result
    assert "Unknown tool" in result["error"]
