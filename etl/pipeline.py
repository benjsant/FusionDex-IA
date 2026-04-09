"""
FusionDex ETL pipeline orchestrator.

Steps:
  1.  extract_pokedex_if       — 501 Pokémon from IF wiki (MediaWiki API)
  2a. extract_stats_pokeapi    — stats + name_fr + evolutions from PokeAPI
  2b. extract_pokepedia_names  — name_en → Pokepedia slug + gen7 URL mapping
  2c. seed_type_effectiveness  — static Gen 7 type chart (18×18 non-neutral rows)
  3.  extract_moves_if         — 644 moves + 121 TMs + tutors from IF wiki
  4.  extract_abilities_if     — ~289 abilities from IF wiki
  5.  extract_locations_if     — locations from IF wiki + Pokédex page
  6.  scrapy (if_movesets)     — movesets from Pokepedia (USUL Gen 7)
                                  level_up (USUL col) + tm + breeding + tutor
  7.  transform_merge_movesets — merge base movesets + IF overrides
  8.  load_db                  — load all data into PostgreSQL
  9.  extract_sprites          — download spritesheets from infinitefusion.net
                                  crop 96×96 cells → data/sprites/{h}.{b}.png

Usage:
  python etl/pipeline.py          # skip if data already loaded
  python etl/pipeline.py --force  # force full re-run
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

BASE_DIR    = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
SCRAPER_DIR = BASE_DIR / "pokepedia_scraper"


def run(cmd: Sequence[str], label: str, cwd: Path | None = None) -> None:
    print(f"\n▶ {label}", flush=True)
    result = subprocess.run(cmd, shell=False, check=False, cwd=cwd)
    if result.returncode != 0:
        print(f"[FAIL] {label}", flush=True)
        sys.exit(1)


def check_already_loaded() -> bool:
    """Return True if pokemon table already has data."""
    try:
        import psycopg2  # noqa: PLC0415

        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "fusiondex_db"),
            user=os.getenv("POSTGRES_USER", "fusiondex_user"),
            password=os.getenv("POSTGRES_PASSWORD", "fusiondex_password"),
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM pokemon;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception:
        return False


def main(force: bool = False) -> None:
    if check_already_loaded() and not force:
        print("[ETL] Data already loaded. Skipping (use --force to rerun).")
        return

    print("[ETL] Starting FusionDex pipeline...", flush=True)

    # Step 1 — Pokédex list from IF wiki
    run(
        ["python", str(SCRIPTS_DIR / "extract_pokedex_if.py")],
        "Step 1/8 — Extract Pokédex from IF wiki",
    )

    # Step 2a — Stats + name_fr + evolutions from PokeAPI
    run(
        ["python", str(SCRIPTS_DIR / "extract_stats_pokeapi.py")],
        "Step 2a/8 — Enrich via PokeAPI (stats, FR names, evolutions)",
    )

    # Step 2b — Pokepedia name mapping (name_en → slug + gen7 URL)
    run(
        ["python", str(SCRIPTS_DIR / "extract_pokepedia_names.py")],
        "Step 2b/8 — Build Pokepedia name mapping",
    )

    # Step 3 — Moves, TMs, tutors from IF wiki
    run(
        ["python", str(SCRIPTS_DIR / "extract_moves_if.py")],
        "Step 3/8 — Extract moves/TMs/tutors from IF wiki",
    )

    # Step 4 — Abilities from IF wiki
    run(
        ["python", str(SCRIPTS_DIR / "extract_abilities_if.py")],
        "Step 4/8 — Extract abilities from IF wiki",
    )

    # Step 5 — Locations from IF wiki
    run(
        ["python", str(SCRIPTS_DIR / "extract_locations_if.py")],
        "Step 5/8 — Extract locations from IF wiki",
    )

    # Step 6 — Pokepedia moveset scraper (USUL, Gen 7)
    # Scrapes: level_up (USUL column) + tm + breeding + tutor for ALL Pokémon
    run(
        ["scrapy", "crawl", "if_movesets"],
        "Step 6/8 — Scrape Pokepedia movesets (USUL Gen 7 — level/tm/breeding/tutor)",
        cwd=SCRAPER_DIR,
    )

    # Step 7 — Merge base movesets with IF-specific overrides
    run(
        ["python", str(SCRIPTS_DIR / "transform_merge_movesets.py")],
        "Step 7/8 — Merge movesets (base + IF overrides)",
    )

    # Step 8 — Load everything into PostgreSQL
    run(
        ["python", str(SCRIPTS_DIR / "load_db.py")],
        "Step 8/9 — Load all data into PostgreSQL",
    )

    # Step 9 — Seed types FR + type effectiveness (après load_db pour DO UPDATE name_fr)
    run(
        ["python", str(SCRIPTS_DIR / "seed_type_effectiveness.py")],
        "Step 9/9 — Seed types FR + type effectiveness chart (Gen 7 / IF)",
    )

    # Step 10 — Download & extract fusion sprites from infinitefusion.net
    run(
        ["python", str(SCRIPTS_DIR / "extract_sprites.py")],
        "Step 10/10 — Download spritesheets & extract sprites (infinitefusion.net)",
    )

    print("\n[ETL] Pipeline completed successfully.", flush=True)


if __name__ == "__main__":
    main(force="--force" in sys.argv)
