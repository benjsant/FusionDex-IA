from sqlalchemy import Column, Integer, String, Text

from backend.db.base import Base


class Item(Base):
    """Game item (scope restreint : fusion / evolution / valuable).

    Source : https://infinitefusion.fandom.com/wiki/List_of_Items
    """

    __tablename__ = "item"

    id         = Column(Integer, primary_key=True)
    name_en    = Column(String(100), nullable=False, unique=True)
    name_fr    = Column(String(100))
    category   = Column(String(20), nullable=False)  # 'fusion' | 'evolution' | 'valuable'
    effect     = Column(Text)
    price_buy  = Column(Integer)
    price_sell = Column(Integer)
