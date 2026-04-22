"""API routes for items (scope restreint : fusion / evolution / valuable)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.item import ItemOut
from backend.services.item_service import get_item_by_id, list_items, search_items

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("/", response_model=list[ItemOut])
def get_items(
    category: str | None = Query(None, pattern="^(fusion|evolution|valuable)$"),
    db: Session = Depends(get_db),
):
    """Liste les items, filtrable par catégorie (fusion / evolution / valuable)."""
    return list_items(db, category=category)


@router.get("/search", response_model=list[ItemOut])
def search_items_route(
    q: str = Query(..., min_length=1, description="Nom partiel EN ou FR (insensible aux accents)"),
    db: Session = Depends(get_db),
):
    """Recherche accent-insensitive sur nom EN ou FR."""
    return search_items(db, q)


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Détail d'un item."""
    item = get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
