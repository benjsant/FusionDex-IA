"""Triple fusion queries."""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from backend.db.models.triple_fusion import (
    TripleFusion,
    TripleFusionAbility,
    TripleFusionComponent,
    TripleFusionType,
)


def list_triple_fusions(db: Session) -> list[TripleFusion]:
    return (
        db.query(TripleFusion)
        .options(
            joinedload(TripleFusion.types).joinedload(TripleFusionType.type),
        )
        .order_by(TripleFusion.id)
        .all()
    )


def get_triple_fusion(db: Session, tf_id: int) -> TripleFusion | None:
    return (
        db.query(TripleFusion)
        .options(
            joinedload(TripleFusion.types).joinedload(TripleFusionType.type),
            joinedload(TripleFusion.components).joinedload(TripleFusionComponent.pokemon),
            joinedload(TripleFusion.abilities).joinedload(TripleFusionAbility.ability),
        )
        .filter(TripleFusion.id == tf_id)
        .first()
    )
