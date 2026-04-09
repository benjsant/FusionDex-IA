from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from backend.db.base import Base


class Generation(Base):
    __tablename__ = "generation"

    id      = Column(Integer, primary_key=True)
    name_en = Column(String(30), nullable=False, unique=True)
    name_fr = Column(String(30), nullable=False, unique=True)

    pokemon = relationship("Pokemon", back_populates="generation")
