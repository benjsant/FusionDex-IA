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


class TMLocationOut(BaseModel):
    """Un lieu où un TM peut être trouvé."""
    location_id: int
    location_name_en: str
    location_name_fr: str | None
    notes: str | None

    model_config = {"from_attributes": True}


class TMInfo(BaseModel):
    """Informations TM pour un move (si ce move est un TM)."""
    number: int                      # 1 = TM01, 121 = TM121
    location_summary: str | None     # résumé texte prêt à afficher
    locations: list[TMLocationOut]   # lieux structurés (0..N)

    model_config = {"from_attributes": True}


class MoveDetail(MoveListItem):
    description_en: str | None
    description_fr: str | None
    source: str         # base | infinite_fusion
    tm: TMInfo | None = None    # null si ce move n'est pas un TM


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


class MoveTutorOut(BaseModel):
    """A NPC that teaches a specific move, with location and price.

    `price` is NULL when `currency` is 'free' or 'quest'.
    """
    id: int
    move_id: int
    location_id: int
    location_name_en: str
    location_name_fr: str | None
    price: int | None
    currency: str                  # 'pokedollars' | 'free' | 'quest'
    npc_description: str | None

    model_config = {"from_attributes": True}
