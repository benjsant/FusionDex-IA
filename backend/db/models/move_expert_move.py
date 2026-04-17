from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from backend.db.base import Base


class MoveExpertMove(Base):
    __tablename__ = "move_expert_move"

    id                   = Column(Integer, primary_key=True)
    move_id              = Column(Integer, ForeignKey("move.id", ondelete="CASCADE"), nullable=False)
    expert_location      = Column(String(20), nullable=False)  # 'knot_island' | 'boon_island'
    required_pokemon_ids = Column(ARRAY(Integer), nullable=False, default=list)  # OR
    required_type_ids    = Column(ARRAY(Integer), nullable=False, default=list)  # AND
    required_move_ids    = Column(ARRAY(Integer), nullable=False, default=list)  # OR

    move = relationship("Move")
