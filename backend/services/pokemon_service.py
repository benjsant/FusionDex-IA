from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from backend.db.models import Move, Pokemon, PokemonEvolution, PokemonMove, Type, TypeEffectiveness


def list_pokemon(db: Session) -> list[Pokemon]:
    return (
        db.query(Pokemon)
        .options(joinedload(Pokemon.types))
        .order_by(Pokemon.id)
        .all()
    )


def get_pokemon_by_id(db: Session, pokemon_id: int) -> Pokemon | None:
    return (
        db.query(Pokemon)
        .options(
            joinedload(Pokemon.types),
            joinedload(Pokemon.abilities),
        )
        .filter(Pokemon.id == pokemon_id)
        .first()
    )


def search_pokemon(db: Session, name: str) -> list[Pokemon]:
    return (
        db.query(Pokemon)
        .options(joinedload(Pokemon.types))
        .filter(
            Pokemon.name_en.ilike(f"%{name}%")
            | Pokemon.name_fr.ilike(f"%{name}%")
        )
        .order_by(Pokemon.id)
        .all()
    )


def compute_pokemon_weaknesses(db: Session, pokemon_id: int) -> list[dict] | None:
    """
    Returns damage multipliers for every attacking type against this Pokémon.

    For dual-type Pokémon the multipliers are compounded:
      e.g. Grass/Flying vs Fire → 0.5 × 2.0 = 1.0 (neutral)

    Only types with a non-neutral final multiplier (≠ 1.0) are returned.
    Types not listed in type_effectiveness default to 1.0.
    """
    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if not pokemon:
        return None

    defending_type_ids = [pt.type_id for pt in pokemon.types]

    multipliers: dict[int, Decimal] = defaultdict(lambda: Decimal("1.0"))

    affinities = (
        db.query(TypeEffectiveness)
        .filter(TypeEffectiveness.defending_type_id.in_(defending_type_ids))
        .all()
    )

    for eff in affinities:
        multipliers[eff.attacking_type_id] *= eff.multiplier

    # Only return non-neutral results
    type_map = {t.id: t for t in db.query(Type).all()}

    return [
        {
            "attacking_type_id":      tid,
            "attacking_type_name_en": type_map[tid].name_en,
            "attacking_type_name_fr": type_map[tid].name_fr,
            "multiplier":             float(mult),
        }
        for tid, mult in sorted(multipliers.items())
        if mult != Decimal("1.0") and tid in type_map
    ]


def get_pokemon_moves(db: Session, pokemon_id: int) -> list[PokemonMove]:
    """All moves for a Pokémon, with move + type eagerly loaded."""
    return (
        db.query(PokemonMove)
        .options(
            joinedload(PokemonMove.move).joinedload(Move.type)
        )
        .filter(PokemonMove.pokemon_id == pokemon_id)
        .order_by(PokemonMove.method, PokemonMove.level)
        .all()
    )


def get_pokemon_evolutions(db: Session, pokemon_id: int) -> list[PokemonEvolution]:
    """Evolution rows from a given Pokémon, with target name eagerly loaded."""
    return (
        db.query(PokemonEvolution)
        .options(joinedload(PokemonEvolution.evolves_into))
        .filter(PokemonEvolution.pokemon_id == pokemon_id)
        .all()
    )
