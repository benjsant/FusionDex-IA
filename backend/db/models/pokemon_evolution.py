from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.db.base import Base


class PokemonEvolution(Base):
    __tablename__ = "pokemon_evolution"

    id              = Column(Integer, primary_key=True)
    pokemon_id      = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    evolves_into_id = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    trigger_type    = Column(String(20), nullable=False)
    # level_up | use_item | trade | friendship | other
    min_level       = Column(Integer)
    item_name_en    = Column(String(100))
    item_name_fr    = Column(String(100))
    if_override     = Column(Boolean, nullable=False, default=False)
    if_notes        = Column(Text)   # description lisible de la condition IF

    pokemon      = relationship("Pokemon", foreign_keys=[pokemon_id],
                                back_populates="evolutions_from")
    evolves_into = relationship("Pokemon", foreign_keys=[evolves_into_id],
                                back_populates="evolutions_into")
