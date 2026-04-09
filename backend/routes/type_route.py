"""API routes for types."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.type_ import TypeOut
from backend.services.type_service import (
    find_type_by_name,
    get_type_by_id,
    list_types,
)

router = APIRouter(prefix="/types", tags=["Types"])


@router.get("/", response_model=list[TypeOut])
def get_types(db: Session = Depends(get_db)):
    """Liste les 27 types IF (18 standard + 9 triple-fusion)."""
    return list_types(db)


@router.get("/by-name/{name}", response_model=TypeOut)
def get_type_by_name(name: str, db: Session = Depends(get_db)):
    """Trouve un type par nom EN ou FR (insensible aux accents, préfixe)."""
    t = find_type_by_name(db, name)
    if not t:
        raise HTTPException(status_code=404, detail=f"Type '{name}' not found")
    return t


@router.get("/{type_id}", response_model=TypeOut)
def get_type(type_id: int, db: Session = Depends(get_db)):
    """Type par ID."""
    t = get_type_by_id(db, type_id)
    if not t:
        raise HTTPException(status_code=404, detail="Type not found")
    return t
