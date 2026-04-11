"""
ETL — Enrich abilities with French names and descriptions from PokeAPI.

Reads  : data/abilities_if.json  (178 abilities, name_en only)
Writes : data/abilities_if.json  (in-place, adds name_fr + description_fr)

Slug rule: name_en.lower().replace(' ', '-')
Version priority for description: ultra-sun-ultra-moon > sun-moon > omega-ruby-alpha-sapphire > x-y
"""

from __future__ import annotations

import json
from pathlib import Path

from etl.utils.logging import setup_logging
from etl.utils.pokeapi import (
    enrich_items_parallel,
    fetch_fr_translation,
    sleep_between_requests,
)

LOGGER = setup_logging(__name__)

POKEAPI      = "https://pokeapi.co/api/v2/ability/{slug}"
DATA_FILE    = Path("data/abilities_if.json")
SAVE_EVERY   = 50
MAX_WORKERS  = 4
REQUEST_DELAY = 0.05
VERSION_PRIO = ["ultra-sun-ultra-moon", "sun-moon", "omega-ruby-alpha-sapphire", "x-y"]

# Manual slug overrides for cases where IF wiki name differs from PokeAPI slug
MANUAL_SLUGS: dict[str, str] = {}


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "")


def _enrich_one(ability: dict) -> tuple[dict, str | None, str | None]:
    name_en = ability["name_en"]
    slug    = MANUAL_SLUGS.get(name_en, slugify(name_en))
    name_fr, desc_fr = fetch_fr_translation(
        POKEAPI.format(slug=slug), VERSION_PRIO, logger=LOGGER,
    )
    sleep_between_requests(REQUEST_DELAY)
    return ability, name_fr, desc_fr


def main() -> None:
    abilities: list[dict] = json.loads(DATA_FILE.read_text())

    to_enrich = [a for a in abilities if a.get("name_fr") is None]
    LOGGER.info("%d abilities à enrichir (sur %d)", len(to_enrich), len(abilities))

    def save() -> None:
        DATA_FILE.write_text(json.dumps(abilities, ensure_ascii=False, indent=2))

    found, not_found = enrich_items_parallel(
        to_enrich,
        _enrich_one,
        save=save,
        logger=LOGGER,
        save_every=SAVE_EVERY,
        max_workers=MAX_WORKERS,
        label="abilities",
    )

    LOGGER.info("Terminé — %d FR trouvés | %d non trouvés", found, len(not_found))
    if not_found:
        LOGGER.warning("Non trouvés: %s", not_found)


if __name__ == "__main__":
    main()
