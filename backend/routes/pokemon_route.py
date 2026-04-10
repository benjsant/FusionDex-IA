from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.evolution import EvolutionOut
from backend.schemas.location import LocationOut
from backend.schemas.move import PokemonMoveOut
from backend.schemas.pokemon import AbilityOut, PokemonDetail, PokemonListItem, TypeOut
from backend.schemas.weakness import WeaknessOut
from backend.services.pokemon_service import (
    compute_pokemon_weaknesses,
    get_pokemon_by_id,
    get_pokemon_evolutions,
    get_pokemon_locations,
    get_pokemon_moves,
    list_pokemon,
    search_pokemon,
)

router = APIRouter(prefix="/pokemon", tags=["Pokemon"])


def _serialize_types(types_rel) -> list[TypeOut]:
    return [
        TypeOut(
            slot=pt.slot,
            name_en=pt.type.name_en,
            name_fr=pt.type.name_fr,
        )
        for pt in sorted(types_rel, key=lambda x: x.slot)
    ]


def _serialize_abilities(abilities_rel) -> list[AbilityOut]:
    return [
        AbilityOut(
            slot=pa.slot,
            is_hidden=pa.is_hidden,
            name_en=pa.ability.name_en,
            name_fr=pa.ability.name_fr,
        )
        for pa in sorted(abilities_rel, key=lambda x: x.slot)
    ]


@router.get("/", response_model=list[PokemonListItem])
def get_pokemon_list(db: Session = Depends(get_db)):
    """Liste tous les Pokémon du jeu Infinite Fusion."""
    pokemons = list_pokemon(db)
    return [
        PokemonListItem(
            id=p.id,
            national_id=p.national_id,
            name_en=p.name_en,
            name_fr=p.name_fr,
            types=_serialize_types(p.types),
            sprite_path=p.sprite_path,
            is_hoenn_only=p.is_hoenn_only,
            pokepedia_url=p.pokepedia_url,
        )
        for p in pokemons
    ]


@router.get("/search", response_model=list[PokemonListItem])
def search_pokemon_route(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Recherche par nom anglais ou français (accent-insensitive)."""
    pokemons = search_pokemon(db, q)
    return [
        PokemonListItem(
            id=p.id,
            national_id=p.national_id,
            name_en=p.name_en,
            name_fr=p.name_fr,
            types=_serialize_types(p.types),
            sprite_path=p.sprite_path,
            is_hoenn_only=p.is_hoenn_only,
            pokepedia_url=p.pokepedia_url,
        )
        for p in pokemons
    ]


@router.get("/{pokemon_id}", response_model=PokemonDetail)
def get_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    """Fiche détaillée d'un Pokémon par son IF ID."""
    p = get_pokemon_by_id(db, pokemon_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    return PokemonDetail(
        id=p.id,
        national_id=p.national_id,
        name_en=p.name_en,
        name_fr=p.name_fr,
        generation_id=p.generation_id,
        hp=p.hp,
        attack=p.attack,
        defense=p.defense,
        sp_attack=p.sp_attack,
        sp_defense=p.sp_defense,
        speed=p.speed,
        base_experience=p.base_experience,
        is_hoenn_only=p.is_hoenn_only,
        sprite_path=p.sprite_path,
        pokepedia_url=p.pokepedia_url,
        types=_serialize_types(p.types),
        abilities=_serialize_abilities(p.abilities),
    )


@router.get("/{pokemon_id}/moves", response_model=list[PokemonMoveOut])
def get_moves_for_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    """Moveset complet d'un Pokémon (level_up, tm, breeding, tutor)."""
    p = get_pokemon_by_id(db, pokemon_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pokémon not found")

    from backend.schemas.type_ import TypeOut as TypeOutMove
    rows = get_pokemon_moves(db, pokemon_id)
    return [
        PokemonMoveOut(
            move_id=r.move_id,
            name_en=r.move.name_en,
            name_fr=r.move.name_fr,
            category=r.move.category,
            power=r.move.power,
            accuracy=r.move.accuracy,
            pp=r.move.pp,
            type=TypeOutMove(
                id=r.move.type.id,
                name_en=r.move.type.name_en,
                name_fr=r.move.type.name_fr,
                is_triple_fusion_type=r.move.type.is_triple_fusion_type,
            ),
            method=r.method,
            level=r.level,
            source=r.source,
        )
        for r in rows
    ]


@router.get("/{pokemon_id}/evolutions", response_model=list[EvolutionOut])
def get_evolutions_for_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    """Chaîne d'évolutions d'un Pokémon."""
    p = get_pokemon_by_id(db, pokemon_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pokémon not found")

    rows = get_pokemon_evolutions(db, pokemon_id)
    return [
        EvolutionOut(
            id=r.id,
            pokemon_id=r.pokemon_id,
            evolves_into_id=r.evolves_into_id,
            evolves_into_name_en=r.evolves_into.name_en,
            evolves_into_name_fr=r.evolves_into.name_fr,
            trigger_type=r.trigger_type,
            min_level=r.min_level,
            item_name_en=r.item_name_en,
            item_name_fr=r.item_name_fr,
            if_override=r.if_override,
            if_notes=r.if_notes,
        )
        for r in rows
    ]


@router.get("/{pokemon_id}/locations", response_model=list[LocationOut])
def get_locations_for_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    """Lieux d'encounter d'un Pokémon (wild, static, legendary…)."""
    p = get_pokemon_by_id(db, pokemon_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    rows = get_pokemon_locations(db, pokemon_id)
    return [
        LocationOut(
            location_id=r.location_id,
            location_name=r.location.name_en,
            method=r.method,
            notes=r.notes,
        )
        for r in rows
    ]


@router.get("/{pokemon_id}/weaknesses", response_model=list[WeaknessOut])
def get_weaknesses_for_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    """Multiplicateurs de dégâts par type attaquant (non-neutres uniquement)."""
    result = compute_pokemon_weaknesses(db, pokemon_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    return result
