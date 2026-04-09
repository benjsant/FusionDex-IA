"""Fusion stat computation service.

Formulas (Pokémon Infinite Fusion):
  Physical stats (HP, Attack, Defense, Speed) = floor(Body×2/3 + Head×1/3)
  Special stats (Sp.Atk, Sp.Def)              = floor(Head×2/3 + Body×1/3)

Types:
  type1 = Head's primary type (slot 1)
  type2 = Body's primary type (slot 1), omitted if identical to type1
"""

from __future__ import annotations

import math

from sqlalchemy.orm import Session, joinedload

from backend.db.models import Pokemon, PokemonType


def compute_fusion(
    db: Session,
    head_id: int,
    body_id: int,
) -> dict | None:
    """
    Returns a dict with computed fusion stats, types, and sprite path.
    Returns None if either Pokémon is not found.
    """
    head = (
        db.query(Pokemon)
        .options(joinedload(Pokemon.types).joinedload(PokemonType.type))
        .filter(Pokemon.id == head_id)
        .first()
    )
    body = (
        db.query(Pokemon)
        .options(joinedload(Pokemon.types).joinedload(PokemonType.type))
        .filter(Pokemon.id == body_id)
        .first()
    )

    if not head or not body:
        return None

    # ── Stats ────────────────────────────────────────────────────────────────
    def phys(b: int, h: int) -> int:
        return math.floor(b * 2 / 3 + h * 1 / 3)

    def spec(h: int, b: int) -> int:
        return math.floor(h * 2 / 3 + b * 1 / 3)

    hp       = phys(body.hp,        head.hp)
    attack   = phys(body.attack,    head.attack)
    defense  = phys(body.defense,   head.defense)
    speed    = phys(body.speed,     head.speed)
    sp_attack  = spec(head.sp_attack,  body.sp_attack)
    sp_defense = spec(head.sp_defense, body.sp_defense)

    # ── Types ─────────────────────────────────────────────────────────────────
    head_types = sorted(head.types, key=lambda pt: pt.slot)
    body_types = sorted(body.types, key=lambda pt: pt.slot)

    type1_obj = head_types[0].type if head_types else None
    type2_obj = body_types[0].type if body_types else None

    # Drop type2 if identical to type1
    if type1_obj and type2_obj and type1_obj.id == type2_obj.id:
        type2_obj = None

    return {
        "head_id":       head_id,
        "body_id":       body_id,
        "head_name_en":  head.name_en,
        "head_name_fr":  head.name_fr,
        "body_name_en":  body.name_en,
        "body_name_fr":  body.name_fr,
        "hp":            hp,
        "attack":        attack,
        "defense":       defense,
        "sp_attack":     sp_attack,
        "sp_defense":    sp_defense,
        "speed":         speed,
        "type1":         type1_obj,
        "type2":         type2_obj,
        "sprite_path":   f"{head_id}.{body_id}.png",
    }
