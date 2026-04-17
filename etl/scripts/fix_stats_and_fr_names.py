"""
Script de correction — re-synchronise stats + name_fr + base_experience
avec le `national_id` (désormais correct après `fix_national_ids.py`).

Le script d'origine (extract_stats_pokeapi.py) posait `national_id = if_id`,
ce qui a mélangé les stats et les noms français pour ~320 lignes. Maintenant
que `national_id` est correct en base, on re-fetch directement depuis PokeAPI.

Aucun fichier intermédiaire : on lit/écrit directement la DB.
"""

from __future__ import annotations

import time

import requests

from etl.utils.db import pg_connection
from etl.utils.logging import setup_logging

LOGGER = setup_logging(__name__)

POKEAPI_POKEMON = "https://pokeapi.co/api/v2/pokemon/{}"
POKEAPI_SPECIES = "https://pokeapi.co/api/v2/pokemon-species/{}"
REQUEST_DELAY = 0.1

STAT_MAP = {
    "hp":              "hp",
    "attack":          "attack",
    "defense":         "defense",
    "special-attack":  "sp_attack",
    "special-defense": "sp_defense",
    "speed":           "speed",
}


def fetch_pokemon(national_id: int) -> dict | None:
    resp = requests.get(POKEAPI_POKEMON.format(national_id), timeout=10)
    if resp.status_code != 200:
        return None
    return resp.json()


def fetch_species(national_id: int) -> dict | None:
    resp = requests.get(POKEAPI_SPECIES.format(national_id), timeout=10)
    if resp.status_code != 200:
        return None
    return resp.json()


def extract_name_fr(species: dict) -> str | None:
    for entry in species.get("names", []):
        if entry["language"]["name"] == "fr":
            return entry["name"]
    return None


def extract_stats(pokemon: dict) -> dict[str, int]:
    return {
        STAT_MAP[s["stat"]["name"]]: s["base_stat"]
        for s in pokemon["stats"]
        if s["stat"]["name"] in STAT_MAP
    }


def fix(conn) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, national_id, name_en FROM pokemon "
        "WHERE national_id IS NOT NULL ORDER BY id"
    )
    rows = cur.fetchall()
    LOGGER.info("%d Pokémon à mettre à jour", len(rows))

    updated = errors = 0
    for i, (pokemon_id, national_id, name_en) in enumerate(rows, start=1):
        poke = fetch_pokemon(national_id)
        time.sleep(REQUEST_DELAY)
        if not poke:
            LOGGER.warning("PokeAPI /pokemon/%d KO pour id=%d (%s)",
                           national_id, pokemon_id, name_en)
            errors += 1
            continue

        species = fetch_species(national_id)
        time.sleep(REQUEST_DELAY)
        name_fr = extract_name_fr(species) if species else None

        stats = extract_stats(poke)
        base_xp = poke.get("base_experience")

        cur.execute(
            """
            UPDATE pokemon SET
                hp              = %(hp)s,
                attack          = %(attack)s,
                defense         = %(defense)s,
                sp_attack       = %(sp_attack)s,
                sp_defense      = %(sp_defense)s,
                speed           = %(speed)s,
                base_experience = %(base_xp)s,
                name_fr         = COALESCE(%(name_fr)s, name_fr)
            WHERE id = %(id)s
            """,
            {
                **stats,
                "base_xp": base_xp,
                "name_fr": name_fr,
                "id":      pokemon_id,
            },
        )
        updated += 1

        if i % 50 == 0:
            conn.commit()
            LOGGER.info("[%d/%d] %d mis à jour, %d erreurs", i, len(rows), updated, errors)

    conn.commit()
    cur.close()
    LOGGER.info("Terminé — %d mis à jour | %d erreurs", updated, errors)


def main() -> None:
    with pg_connection() as conn:
        fix(conn)


if __name__ == "__main__":
    main()
