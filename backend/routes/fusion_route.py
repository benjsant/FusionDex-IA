"""API routes for fusion computation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.fusion import FusionResult
from backend.schemas.type_ import TypeOut
from backend.services.fusion_service import compute_fusion

router = APIRouter(prefix="/fusion", tags=["Fusion"])


@router.get("/{head_id}/{body_id}", response_model=FusionResult)
def get_fusion(head_id: int, body_id: int, db: Session = Depends(get_db)):
    """
    Calcule les stats, types et sprite d'une fusion.

    - Stats physiques (HP/Atk/Def/Spe) = floor(Body×2/3 + Head×1/3)
    - Stats spéciales (SpA/SpD)         = floor(Head×2/3 + Body×1/3)
    - Type 1 = type principal de Head
    - Type 2 = type principal de Body (si différent)
    - Sprite : `{head_id}.{body_id}.png`
    """
    result = compute_fusion(db, head_id, body_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pokémon #{head_id} or #{body_id} not found",
        )

    def to_type_out(t) -> TypeOut | None:
        if t is None:
            return None
        return TypeOut(
            id=t.id,
            name_en=t.name_en,
            name_fr=t.name_fr,
            is_triple_fusion_type=t.is_triple_fusion_type,
        )

    return FusionResult(
        head_id=result["head_id"],
        body_id=result["body_id"],
        head_name_en=result["head_name_en"],
        head_name_fr=result["head_name_fr"],
        body_name_en=result["body_name_en"],
        body_name_fr=result["body_name_fr"],
        hp=result["hp"],
        attack=result["attack"],
        defense=result["defense"],
        sp_attack=result["sp_attack"],
        sp_defense=result["sp_defense"],
        speed=result["speed"],
        type1=to_type_out(result["type1"]),
        type2=to_type_out(result["type2"]),
        sprite_path=result["sprite_path"],
    )
