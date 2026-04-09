from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from backend.db.base import Base


class Creator(Base):
    __tablename__ = "creator"

    id   = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)

    sprites = relationship("FusionSpriteCreator", back_populates="creator")
