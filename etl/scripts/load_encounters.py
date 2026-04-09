"""
ETL — Load encounters into location + pokemon_location tables.

Reads : data/encounters_if.json
Writes: location + pokemon_location in PostgreSQL

Name→ID resolution:
  - Wild entries have national_id directly
  - Static/Legendary entries have pokemon_name (EN) → match against pokemon.name_en
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import psycopg2

from etl.utils.db import get_pg_connection as get_connection

LOGGER    = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATA_FILE = Path("data/encounters_if.json")

# method values allowed by DB check constraint
VALID_METHODS = {"wild", "gift", "trade", "static", "fishing", "headbutt"}


def load_encounters(conn) -> None:
    entries: list[dict] = json.loads(DATA_FILE.read_text())
    LOGGER.info("Loaded %d encounter entries", len(entries))

    with conn.cursor() as cur:
        # Build lookup maps
        cur.execute("SELECT id, national_id, name_en FROM pokemon WHERE is_hoenn_only = false")
        by_national: dict[int, int]  = {}
        by_name:     dict[str, int]  = {}
        for db_id, nat_id, name_en in cur.fetchall():
            if nat_id:
                by_national[nat_id] = db_id
            by_name[name_en.lower()] = db_id

        # ── Insert locations ──────────────────────────────────────────────────
        location_names = {e["location_name"] for e in entries if e.get("location_name")}
        for loc_name in sorted(location_names):
            cur.execute(
                "INSERT INTO location (name_en) VALUES (%s) ON CONFLICT (name_en) DO NOTHING",
                (loc_name,),
            )
        conn.commit()

        cur.execute("SELECT id, name_en FROM location")
        loc_map: dict[str, int] = {name: db_id for db_id, name in cur.fetchall()}
        LOGGER.info("Locations: %d", len(loc_map))

        # ── Insert pokemon_location ───────────────────────────────────────────
        inserted  = 0
        skipped   = 0
        no_pokemon = 0

        for e in entries:
            loc_name = e.get("location_name")
            if not loc_name or loc_name not in loc_map:
                skipped += 1
                continue

            loc_id = loc_map[loc_name]
            method = e.get("method", "wild")
            if method not in VALID_METHODS:
                method = "wild"

            # Resolve pokemon_id
            pokemon_id: int | None = None
            if e.get("national_id"):
                pokemon_id = by_national.get(e["national_id"])
            if pokemon_id is None and e.get("pokemon_name"):
                pokemon_id = by_name.get(e["pokemon_name"].lower())

            if pokemon_id is None:
                LOGGER.debug("Cannot resolve Pokémon: %s", e.get("pokemon_name"))
                no_pokemon += 1
                continue

            # Build notes
            notes_parts = []
            if e.get("encounter_rate"):
                notes_parts.append(f"rate:{e['encounter_rate']}")
            if e.get("level_min") is not None:
                lmin, lmax = e["level_min"], e["level_max"]
                notes_parts.append(f"lv:{lmin}-{lmax}" if lmin != lmax else f"lv:{lmin}")
            if e.get("notes"):
                notes_parts.append(e["notes"])
            notes = " | ".join(notes_parts) or None

            try:
                cur.execute(
                    "INSERT INTO pokemon_location (pokemon_id, location_id, method, notes) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (pokemon_id, location_id, method) DO UPDATE SET notes = EXCLUDED.notes",
                    (pokemon_id, loc_id, method, notes),
                )
                inserted += 1
            except psycopg2.Error as exc:
                LOGGER.warning("Insert error for %s @ %s: %s", e.get("pokemon_name"), loc_name, exc)
                conn.rollback()
                skipped += 1

        conn.commit()
        LOGGER.info(
            "pokemon_location: %d inserted/updated | %d no_pokemon | %d skipped",
            inserted, no_pokemon, skipped,
        )


def main() -> None:
    LOGGER.info("Connecting to PostgreSQL...")
    conn = get_connection()
    try:
        load_encounters(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
