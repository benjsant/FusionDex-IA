"""DB coverage / audit stats."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db.models import (
    Ability,
    Creator,
    FusionSprite,
    Move,
    Pokemon,
    PokemonAbility,
    PokemonMove,
    PokemonType,
    TripleFusion,
)


def compute_coverage(db: Session) -> dict:
    pokemon_total = db.query(func.count(Pokemon.id)).scalar()

    no_sprite = (
        db.query(func.count(Pokemon.id))
        .filter((Pokemon.sprite_path.is_(None)) | (Pokemon.sprite_path == ""))
        .scalar()
    )
    no_types = (
        db.query(func.count(Pokemon.id))
        .filter(~Pokemon.id.in_(db.query(PokemonType.pokemon_id)))
        .scalar()
    )
    no_abilities = (
        db.query(func.count(Pokemon.id))
        .filter(~Pokemon.id.in_(db.query(PokemonAbility.pokemon_id)))
        .scalar()
    )
    no_moves = (
        db.query(func.count(Pokemon.id))
        .filter(~Pokemon.id.in_(db.query(PokemonMove.pokemon_id)))
        .scalar()
    )

    moves_total = db.query(func.count(Move.id)).scalar()
    moves_unused = (
        db.query(func.count(Move.id))
        .filter(~Move.id.in_(db.query(PokemonMove.move_id)))
        .scalar()
    )

    abilities_total = db.query(func.count(Ability.id)).scalar()
    abilities_unused = (
        db.query(func.count(Ability.id))
        .filter(~Ability.id.in_(db.query(PokemonAbility.ability_id)))
        .scalar()
    )

    return {
        "pokemon_total": pokemon_total,
        "pokemon_without_sprite": no_sprite,
        "pokemon_without_types": no_types,
        "pokemon_without_abilities": no_abilities,
        "pokemon_without_moves": no_moves,
        "moves_total": moves_total,
        "moves_unused": moves_unused,
        "abilities_total": abilities_total,
        "abilities_unused": abilities_unused,
        "fusion_sprites_total": db.query(func.count(FusionSprite.id)).scalar(),
        "triple_fusions_total": db.query(func.count(TripleFusion.id)).scalar(),
        "creators_total": db.query(func.count(Creator.id)).scalar(),
    }
