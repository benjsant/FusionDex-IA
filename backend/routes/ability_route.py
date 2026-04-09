"""API routes for abilities."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.ability import AbilityDetail, AbilityListItem
from backend.services.ability_service import (
    get_ability_by_id,
    list_abilities,
    search_abilities,
)

router = APIRouter(prefix="/abilities", tags=["Abilities"])


@router.get("/", response_model=list[AbilityListItem])
def get_abilities(db: Session = Depends(get_db)):
    """Liste tous les talents (~289 talents IF)."""
    return list_abilities(db)


@router.get("/search", response_model=list[AbilityListItem])
def search_abilities_route(
    q: str = Query(..., min_length=1, description="Nom partiel EN ou FR (insensible aux accents)"),
    db: Session = Depends(get_db),
):
    """Recherche accent-insensitive sur nom EN ou FR."""
    return search_abilities(db, q)


@router.get("/{ability_id}", response_model=AbilityDetail)
def get_ability(ability_id: int, db: Session = Depends(get_db)):
    """Détail d'un talent avec descriptions EN/FR."""
    ability = get_ability_by_id(db, ability_id)
    if not ability:
        raise HTTPException(status_code=404, detail="Ability not found")
    return ability
