from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from backend.db.base import Base


class Location(Base):
    __tablename__ = "location"

    id      = Column(Integer, primary_key=True)
    name_en = Column(String(200), nullable=False, unique=True)
    name_fr = Column(String(200))
    region  = Column(String(50))   # 'Kanto', 'Johto', 'Other'

    pokemon_locations = relationship("PokemonLocation", back_populates="location")
