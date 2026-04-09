from sqlalchemy import Column, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from backend.db.base import Base


class TypeEffectiveness(Base):
    """
    Damage multiplier when attacking_type attacks defending_type.

    Multipliers:
      0.0 → no effect
      0.5 → not very effective
      1.0 → neutral (rows NOT stored — assumed default)
      2.0 → super effective
    """
    __tablename__ = "type_effectiveness"

    attacking_type_id = Column(
        Integer,
        ForeignKey("type.id", ondelete="CASCADE"),
        primary_key=True,
    )
    defending_type_id = Column(
        Integer,
        ForeignKey("type.id", ondelete="CASCADE"),
        primary_key=True,
    )
    multiplier = Column(Numeric(3, 2), nullable=False)

    attacking_type = relationship("Type", foreign_keys=[attacking_type_id])
    defending_type = relationship("Type", foreign_keys=[defending_type_id])
