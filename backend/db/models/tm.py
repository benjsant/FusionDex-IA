from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from backend.db.base import Base


class TM(Base):
    __tablename__ = "tm"

    id       = Column(Integer, primary_key=True)
    number   = Column(Integer, nullable=False, unique=True)
    move_id  = Column(Integer, ForeignKey("move.id"), nullable=False)
    location = Column(Text)

    move = relationship("Move", back_populates="tm")
