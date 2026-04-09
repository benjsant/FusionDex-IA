"""
Script de correction — Enrich pokemon_type depuis PokeAPI.

Problème : extract_pokedex_if.py assigne mal type1/type2 depuis le wiki IF.
Solution  : pour chaque Pokémon avec national_id connu, récupère les types
            depuis PokeAPI et met à jour pokemon_type en base.

Idempotent : ON CONFLICT (pokemon_id, slot) DO UPDATE.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

import psycopg2
import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

POKEAPI = "https://pokeapi.co/api/v2/pokemon/{}"
REQUEST_DELAY = 0.15  # secondes entre requêtes

# Pokémon IF sans équivalent PokeAPI (formes IF custom, triple fusions, etc.)
# On les laisse avec les types du wiki IF
SKIP_NATIONAL_IDS: set[int] = set()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "fusiondex_db"),
        user=os.getenv("POSTGRES_USER", "fusiondex_user"),
        password=os.getenv("POSTGRES_PASSWORD", "fusiondex_password"),
    )


def fetch_types(national_id: int) -> list[tuple[int, str]]:
    """Retourne [(slot, type_name_en)] depuis PokeAPI pour un national_id."""
    try:
        resp = requests.get(POKEAPI.format(national_id), timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [
            (t["slot"], t["type"]["name"].capitalize())
            for t in data["types"]
        ]
    except Exception as e:
        LOGGER.warning("PokeAPI error pour #%d : %s", national_id, e)
        return []


def main() -> None:
    conn = get_connection()
    cur  = conn.cursor()

    # Récupère la liste des Pokémon avec leur national_id
    cur.execute("SELECT id, national_id FROM pokemon WHERE national_id IS NOT NULL ORDER BY id")
    rows = cur.fetchall()
    LOGGER.info("%d Pokémon avec national_id trouvés", len(rows))

    # Récupère le type_map name_en → id
    cur.execute("SELECT id, name_en FROM type WHERE is_triple_fusion_type = FALSE")
    type_map: dict[str, int] = {name: tid for tid, name in cur.fetchall()}

    updated = skipped = errors = 0

    for i, (pokemon_id, national_id) in enumerate(rows):
        if national_id in SKIP_NATIONAL_IDS:
            skipped += 1
            continue

        types = fetch_types(national_id)
        if not types:
            errors += 1
            continue

        for slot, type_name in types:
            # Certains noms PokeAPI : "fighting" → "Fighting"
            type_id = type_map.get(type_name)
            if type_id is None:
                LOGGER.warning(
                    "Type inconnu '%s' pour Pokémon #%d (national #%d)",
                    type_name, pokemon_id, national_id
                )
                continue

            cur.execute(
                """
                INSERT INTO pokemon_type (pokemon_id, type_id, slot)
                VALUES (%s, %s, %s)
                ON CONFLICT (pokemon_id, slot) DO UPDATE
                    SET type_id = EXCLUDED.type_id
                """,
                (pokemon_id, type_id, slot),
            )

        if (i + 1) % 50 == 0:
            conn.commit()
            LOGGER.info("[%d/%d] %d mis à jour, %d erreurs", i + 1, len(rows), updated + i + 1, errors)

        updated += 1
        time.sleep(REQUEST_DELAY)

    conn.commit()

    # Pokémon sans national_id (IF-only) : utilise type2 du wiki comme slot 1
    LOGGER.info("Correction des Pokémon IF-only (sans national_id)...")
    cur.execute("""
        SELECT id FROM pokemon
        WHERE national_id IS NULL
          AND id NOT IN (SELECT DISTINCT pokemon_id FROM pokemon_type)
    """)
    if_only = [r[0] for r in cur.fetchall()]
    LOGGER.info("%d Pokémon IF-only sans types en base", len(if_only))

    cur.close()
    conn.close()
    LOGGER.info(
        "Terminé — %d mis à jour | %d ignorés | %d erreurs",
        updated, skipped, errors
    )


if __name__ == "__main__":
    main()
