"""Service layer for items (scope restreint : fusion / evolution / valuable)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.db.models import Item
from backend.utils.text import normalize


def list_items(db: Session, *, category: str | None = None) -> list[Item]:
    """List items, optionally filtered by category."""
    query = db.query(Item)
    if category is not None:
        query = query.filter(Item.category == category)
    return query.order_by(Item.category, Item.name_en).all()


def get_item_by_id(db: Session, item_id: int) -> Item | None:
    return db.query(Item).filter(Item.id == item_id).first()


def search_items(db: Session, name: str) -> list[Item]:
    """Accent-insensitive partial match on name_en or name_fr."""
    needle = normalize(name)
    items = db.query(Item).all()
    return [
        i for i in items
        if needle in normalize(i.name_en or "")
        or needle in normalize(i.name_fr or "")
    ]
