"""
ETL — Enrich abilities with French names and descriptions from PokeAPI.

Reads  : data/abilities_if.json  (178 abilities, name_en only)
Writes : data/abilities_if.json  (in-place, adds name_fr + description_fr)

Slug rule: name_en.lower().replace(' ', '-')
Version priority for description: ultra-sun-ultra-moon > sun-moon > omega-ruby-alpha-sapphire > x-y
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

POKEAPI      = "https://pokeapi.co/api/v2/ability/{slug}"
DATA_FILE    = Path("data/abilities_if.json")
SAVE_EVERY   = 50
VERSION_PRIO = ["ultra-sun-ultra-moon", "sun-moon", "omega-ruby-alpha-sapphire", "x-y"]

# Manual slug overrides for cases where IF wiki name differs from PokeAPI slug
MANUAL_SLUGS: dict[str, str] = {}


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "")


def fetch_ability_fr(slug: str) -> tuple[str | None, str | None]:
    """Returns (name_fr, description_fr) or (None, None) on failure."""
    try:
        r = requests.get(POKEAPI.format(slug=slug), timeout=10)
        if r.status_code == 404:
            return None, None
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        LOGGER.warning("Error fetching %s: %s", slug, exc)
        return None, None

    name_fr = next(
        (n["name"] for n in data.get("names", []) if n["language"]["name"] == "fr"),
        None,
    )

    desc_fr = None
    for vg in VERSION_PRIO:
        desc_fr = next(
            (e["flavor_text"] for e in data.get("flavor_text_entries", [])
             if e["language"]["name"] == "fr" and e["version_group"]["name"] == vg),
            None,
        )
        if desc_fr:
            desc_fr = desc_fr.replace("\n", " ").replace("\xa0", " ")
            break

    return name_fr, desc_fr


def main() -> None:
    abilities: list[dict] = json.loads(DATA_FILE.read_text())

    to_enrich = [a for a in abilities if a.get("name_fr") is None]
    LOGGER.info("%d abilities à enrichir (sur %d)", len(to_enrich), len(abilities))

    found = 0
    not_found: list[str] = []

    for i, ability in enumerate(to_enrich, 1):
        name_en = ability["name_en"]
        slug    = MANUAL_SLUGS.get(name_en, slugify(name_en))

        name_fr, desc_fr = fetch_ability_fr(slug)

        if name_fr:
            ability["name_fr"]        = name_fr
            ability["description_fr"] = desc_fr
            found += 1
        else:
            not_found.append(name_en)
            LOGGER.warning("[NOT FOUND] %s (slug: %s)", name_en, slug)

        if i % SAVE_EVERY == 0:
            DATA_FILE.write_text(json.dumps(abilities, ensure_ascii=False, indent=2))
            LOGGER.info("[%d/%d] %d trouvés, %d non trouvés", i, len(to_enrich), found, len(not_found))

        time.sleep(0.3)

    DATA_FILE.write_text(json.dumps(abilities, ensure_ascii=False, indent=2))
    LOGGER.info("Terminé — %d FR trouvés | %d non trouvés", found, len(not_found))
    if not_found:
        LOGGER.warning("Non trouvés: %s", not_found)


if __name__ == "__main__":
    main()
