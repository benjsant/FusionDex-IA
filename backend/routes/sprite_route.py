"""API routes for fusion sprites."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.sprite import SpriteOut
from backend.services.sprite_service import list_sprites_for_pair

router = APIRouter(prefix="/sprites", tags=["Sprites"])


@router.get("/{head_id}/{body_id}", response_model=list[SpriteOut])
def get_sprites_for_pair(
    head_id: int,
    body_id: int,
    db: Session = Depends(get_db),
):
    """
    Liste toutes les variantes de sprite pour une paire head/body,
    avec leurs crédits (créateurs).

    - Le sprite par défaut est trié en premier (is_default=true).
    - `source`: 'local' (auto-généré), 'community' (sprite custom), 'auto_generated'.
    """
    sprites = list_sprites_for_pair(db, head_id, body_id)
    return [
        SpriteOut(
            id=s.id,
            head_id=s.head_id,
            body_id=s.body_id,
            sprite_path=s.sprite_path,
            is_custom=s.is_custom,
            is_default=s.is_default,
            source=s.source,
            creators=[c.creator.name for c in s.creators],
        )
        for s in sprites
    ]
