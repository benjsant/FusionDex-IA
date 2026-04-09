from __future__ import annotations

from pydantic import BaseModel

from backend.schemas.type_ import TypeOut


class FusionResult(BaseModel):
    head_id: int
    body_id: int
    head_name_en: str
    head_name_fr: str | None
    body_name_en: str
    body_name_fr: str | None
    # Computed stats
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int
    # Types: head gives type1, body gives type2
    type1: TypeOut
    type2: TypeOut | None
    # Sprite path pattern: "{head_id}.{body_id}.png"
    sprite_path: str
