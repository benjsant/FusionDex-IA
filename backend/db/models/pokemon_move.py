from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.db.base import Base


class PokemonMove(Base):
    __tablename__ = "pokemon_move"

    id         = Column(Integer, primary_key=True)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id", ondelete="CASCADE"),
                        nullable=False)
    move_id    = Column(Integer, ForeignKey("move.id"), nullable=False)
    method     = Column(String(20), nullable=False)
    # level_up | tm | tutor | breeding | special
    level      = Column(Integer)     # uniquement pour level_up
    source     = Column(String(20), nullable=False, default="base")
    # base | infinite_fusion

    pokemon = relationship("Pokemon", back_populates="moves")
    move    = relationship("Move", back_populates="pokemon_moves")
