from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.db.base import Base


class TM(Base):
    __tablename__ = "tm"

    id       = Column(Integer, primary_key=True)
    number   = Column(Integer, nullable=False, unique=True)
    move_id  = Column(Integer, ForeignKey("move.id"), nullable=False)
    location = Column(Text)  # résumé texte prêt à afficher (ex: "Route 13 (Surf)")

    move      = relationship("Move", back_populates="tm")
    locations = relationship("TMLocation", back_populates="tm", cascade="all, delete-orphan")


class TMLocation(Base):
    """Junction TM ↔ Location (un TM peut être trouvé à plusieurs endroits)."""

    __tablename__ = "tm_location"

    id          = Column(Integer, primary_key=True)
    tm_id       = Column(Integer, ForeignKey("tm.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    notes       = Column(Text)  # "(Surf)", "(Gym)", "(Dept. Store)", ...

    tm       = relationship("TM", back_populates="locations")
    location = relationship("Location")

    __table_args__ = (
        UniqueConstraint("tm_id", "location_id", "notes", name="uq_tm_location"),
    )
