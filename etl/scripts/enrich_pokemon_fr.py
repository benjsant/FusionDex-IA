"""
ETL — Enrich pokemon table with pokepedia_url from pokepedia_names.json.

Reads  : data/pokepedia_names.json  {national_id, name_en, name_fr, pokepedia_slug, gen7_url}
Updates: pokemon.pokepedia_url  (gen7_url from Pokepedia)

Idempotent : only updates rows where pokepedia_url IS NULL.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from etl.utils.db import get_pg_connection as get_connection

LOGGER    = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATA_FILE = Path("data/pokepedia_names.json")


def enrich_pokemon_pokepedia(conn) -> None:
    entries: list[dict] = json.loads(DATA_FILE.read_text())

    # Build lookup: national_id → gen7_url
    by_national: dict[int, str] = {
        e["national_id"]: e["gen7_url"]
        for e in entries
        if e.get("gen7_url") and e.get("national_id")
    }

    cur = conn.cursor()

    # Fetch all pokemon that need enrichment
    cur.execute("SELECT id, national_id FROM pokemon WHERE pokepedia_url IS NULL AND national_id IS NOT NULL")
    rows = cur.fetchall()
    LOGGER.info("%d Pokémon à enrichir (pokepedia_url manquant)", len(rows))

    updated = skipped = 0
    for pokemon_id, national_id in rows:
        url = by_national.get(national_id)
        if not url:
            LOGGER.debug("No pokepedia URL for national_id=%d", national_id)
            skipped += 1
            continue
        cur.execute(
            "UPDATE pokemon SET pokepedia_url = %s WHERE id = %s",
            (url, pokemon_id),
        )
        updated += 1

    conn.commit()
    LOGGER.info("Updated %d Pokémon with pokepedia_url | %d skipped", updated, skipped)


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"{DATA_FILE} not found")
    conn = get_connection()
    try:
        enrich_pokemon_pokepedia(conn)
    except Exception:
        conn.rollback()
        LOGGER.exception("enrich_pokemon_fr failed — rolling back")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
