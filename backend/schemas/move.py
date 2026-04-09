from __future__ import annotations

from pydantic import BaseModel

from backend.schemas.type_ import TypeOut


class MoveListItem(BaseModel):
    id: int
    name_en: str
    name_fr: str | None
    category: str       # Physical | Special | Status
    power: int | None
    accuracy: int | None
    pp: int
    type: TypeOut

    model_config = {"from_attributes": True}


class MoveDetail(MoveListItem):
    description_en: str | None
    description_fr: str | None
    source: str         # base | infinite_fusion


class PokemonMoveOut(BaseModel):
    """Move as learned by a specific Pokémon — includes learning context."""
    move_id: int
    name_en: str
    name_fr: str | None
    category: str
    power: int | None
    accuracy: int | None
    pp: int
    type: TypeOut
    method: str         # level_up | tm | tutor | breeding | special
    level: int | None   # only for level_up
    source: str         # base | infinite_fusion

    model_config = {"from_attributes": True}
