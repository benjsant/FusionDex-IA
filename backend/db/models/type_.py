from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from backend.db.base import Base


class Type(Base):
    __tablename__ = "type"

    id                    = Column(Integer, primary_key=True)
    name_en               = Column(String(30), nullable=False, unique=True)
    name_fr               = Column(String(30))
    is_triple_fusion_type = Column(Boolean, nullable=False, default=False)

    moves         = relationship("Move", back_populates="type")
    pokemon_types = relationship("PokemonType", back_populates="type")
