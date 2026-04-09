"""API routes for moves."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.move import MoveDetail, MoveListItem, PokemonMoveOut
from backend.schemas.type_ import TypeOut
from backend.services.move_service import (
    get_move_by_id,
    list_moves,
    list_moves_by_type,
    search_moves,
)

router = APIRouter(prefix="/moves", tags=["Moves"])


def _move_to_list_item(m) -> MoveListItem:
    return MoveListItem(
        id=m.id,
        name_en=m.name_en,
        name_fr=m.name_fr,
        category=m.category,
        power=m.power,
        accuracy=m.accuracy,
        pp=m.pp,
        type=TypeOut(
            id=m.type.id,
            name_en=m.type.name_en,
            name_fr=m.type.name_fr,
            is_triple_fusion_type=m.type.is_triple_fusion_type,
        ),
    )


@router.get("/", response_model=list[MoveListItem])
def get_moves(db: Session = Depends(get_db)):
    """Liste toutes les capacités (644 moves IF)."""
    return [_move_to_list_item(m) for m in list_moves(db)]


@router.get("/search", response_model=list[MoveListItem])
def search_moves_route(
    q: str = Query(..., min_length=1, description="Nom partiel EN ou FR (insensible aux accents)"),
    db: Session = Depends(get_db),
):
    """Recherche accent-insensitive sur nom EN ou FR."""
    return [_move_to_list_item(m) for m in search_moves(db, q)]


@router.get("/by-type/{type_name}", response_model=list[MoveListItem])
def get_moves_by_type(type_name: str, db: Session = Depends(get_db)):
    """Toutes les capacités d'un type donné (nom EN ou FR, préfixe insensible)."""
    moves = list_moves_by_type(db, type_name)
    if not moves:
        raise HTTPException(status_code=404, detail=f"No moves found for type '{type_name}'")
    return [_move_to_list_item(m) for m in moves]


@router.get("/{move_id}", response_model=MoveDetail)
def get_move(move_id: int, db: Session = Depends(get_db)):
    """Détail complet d'une capacité."""
    move = get_move_by_id(db, move_id)
    if not move:
        raise HTTPException(status_code=404, detail="Move not found")
    return MoveDetail(
        id=move.id,
        name_en=move.name_en,
        name_fr=move.name_fr,
        category=move.category,
        power=move.power,
        accuracy=move.accuracy,
        pp=move.pp,
        description_en=move.description_en,
        description_fr=move.description_fr,
        source=move.source,
        type=TypeOut(
            id=move.type.id,
            name_en=move.type.name_en,
            name_fr=move.type.name_fr,
            is_triple_fusion_type=move.type.is_triple_fusion_type,
        ),
    )
