"""Service layer for moves."""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from backend.db.models import Move, PokemonMove
from backend.utils.text import normalize


def list_moves(
    db: Session,
    *,
    category: str | None = None,
    type_id: int | None = None,
    power_min: int | None = None,
    power_max: int | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Move]:
    query = db.query(Move).options(joinedload(Move.type))
    if category is not None:
        query = query.filter(Move.category == category)
    if type_id is not None:
        query = query.filter(Move.type_id == type_id)
    if power_min is not None:
        query = query.filter(Move.power >= power_min)
    if power_max is not None:
        query = query.filter(Move.power <= power_max)
    query = query.order_by(Move.id).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def get_move_by_id(db: Session, move_id: int) -> Move | None:
    return (
        db.query(Move)
        .options(joinedload(Move.type))
        .filter(Move.id == move_id)
        .first()
    )


def search_moves(db: Session, name: str) -> list[Move]:
    """Accent-insensitive partial match on name_en OR name_fr."""
    needle = normalize(name)
    moves = (
        db.query(Move)
        .options(joinedload(Move.type))
        .all()
    )
    return [
        m for m in moves
        if needle in normalize(m.name_en or "")
        or needle in normalize(m.name_fr or "")
    ]


def list_moves_by_type(db: Session, type_name: str) -> list[Move]:
    """All moves for a given type (name_en or name_fr, accent-insensitive)."""
    needle = normalize(type_name)
    from backend.db.models import Type  # avoid circular at module level

    types = db.query(Type).all()
    type_obj = next(
        (t for t in types if normalize(t.name_en or "").startswith(needle)
         or normalize(t.name_fr or "").startswith(needle)),
        None,
    )
    if not type_obj:
        return []

    return (
        db.query(Move)
        .options(joinedload(Move.type))
        .filter(Move.type_id == type_obj.id)
        .order_by(Move.id)
        .all()
    )


def list_pokemon_moves(db: Session, pokemon_id: int) -> list[PokemonMove]:
    """All PokemonMove rows for a Pokémon, with move + type eagerly loaded."""
    return (
        db.query(PokemonMove)
        .options(
            joinedload(PokemonMove.move).joinedload(Move.type)
        )
        .filter(PokemonMove.pokemon_id == pokemon_id)
        .order_by(PokemonMove.method, PokemonMove.level)
        .all()
    )
