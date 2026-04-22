from __future__ import annotations

from pydantic import BaseModel


class ItemOut(BaseModel):
    """A game item (scope restreint : fusion / evolution / valuable)."""
    id: int
    name_en: str
    name_fr: str | None
    category: str              # 'fusion' | 'evolution' | 'valuable'
    effect: str | None
    price_buy: int | None      # Pokédollars, NULL si non vendu
    price_sell: int | None     # Pokédollars, NULL si non revendable

    model_config = {"from_attributes": True}
