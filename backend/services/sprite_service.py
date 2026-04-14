"""Sprite lookup service."""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from backend.db.models import FusionSprite, FusionSpriteCreator


def list_sprites_for_pair(db: Session, head_id: int, body_id: int) -> list[FusionSprite]:
    return (
        db.query(FusionSprite)
        .options(
            joinedload(FusionSprite.creators).joinedload(FusionSpriteCreator.creator)
        )
        .filter(FusionSprite.head_id == head_id, FusionSprite.body_id == body_id)
        .order_by(FusionSprite.is_default.desc(), FusionSprite.sprite_path)
        .all()
    )
