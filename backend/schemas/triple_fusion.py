from __future__ import annotations

from pydantic import BaseModel


class TripleFusionComponentOut(BaseModel):
    position: int
    pokemon_id: int
    name_en: str
    name_fr: str | None


class TripleFusionTypeOut(BaseModel):
    slot: int
    name_en: str
    name_fr: str | None
    is_triple_fusion_type: bool


class TripleFusionAbilityOut(BaseModel):
    slot: int
    is_hidden: bool
    name_en: str
    name_fr: str | None


class TripleFusionListItem(BaseModel):
    id: int
    name_en: str
    name_fr: str | None
    sprite_path: str | None
    types: list[TripleFusionTypeOut]


class TripleFusionDetail(TripleFusionListItem):
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int
    evolves_from_id: int | None
    evolution_level: int | None
    steps_to_hatch: int | None
    components: list[TripleFusionComponentOut]
    abilities: list[TripleFusionAbilityOut]
