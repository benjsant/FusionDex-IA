from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from backend.db.base import Base


class PokemonType(Base):
    __tablename__ = "pokemon_type"

    pokemon_id  = Column(Integer, ForeignKey("pokemon.id", ondelete="CASCADE"),
                         primary_key=True)
    type_id     = Column(Integer, ForeignKey("type.id"), primary_key=True)
    slot        = Column(Integer, nullable=False)   # 1 ou 2
    if_override = Column(Boolean, nullable=False, default=False)

    pokemon = relationship("Pokemon", back_populates="types")
    type    = relationship("Type", back_populates="pokemon_types")
