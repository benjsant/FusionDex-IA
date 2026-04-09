"""
ETL Step 1 — Extract Pokédex from Infinite Fusion wiki (MediaWiki API).

Fetches the Pokédex page and parses all 501 Pokémon entries:
  - IF internal ID
  - Name (EN)
  - Type1, Type2
  - Generation
  - Location (raw string)
  - Hoenn-only flag

Output: data/pokedex_if.json
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from etl.utils.http import get_json

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

WIKI_API = "https://infinitefusion.fandom.com/api.php"
OUTPUT   = Path("data/pokedex_if.json")

# Template pattern inside wikitext:
# {{PokedexTable/Data|index|id|name|type1|type2|location|notes}}
ENTRY_RE = re.compile(
    r"\{\{PokedexTable/Data\s*\|"
    r"\s*(?P<index>\d+)\s*\|"
    r"\s*(?P<id>\d+)\s*\|"
    r"\s*(?P<name>[^|]+?)\s*\|"
    r"\s*(?P<type1>[^|]*?)\s*\|"
    r"\s*(?P<type2>[^|]*?)\s*\|"
    r"\s*(?P<location>[^|]*?)\s*\|?"
    r"(?P<notes>[^}]*)?\}\}",
    re.IGNORECASE,
)

# Pokémon marked "Not in game" / "Hoenn only"
HOENN_ONLY_RE = re.compile(r"not in game|hoenn", re.IGNORECASE)

# Generation boundaries (IF Pokédex index → gen number)
# Gen 1: index 1-151 / Gen 2: 152-251 / Gen 3+: 252+
GEN_BOUNDARIES = [
    (1,   151, 1),
    (152, 251, 2),
    (252, 999, 3),   # Gen 3-7 grouped initially; refined later via PokeAPI national_id
]


def detect_generation(index: int) -> int:
    for start, end, gen in GEN_BOUNDARIES:
        if start <= index <= end:
            return gen
    return 3


def clean_wikitext(text: str) -> str:
    """Strip wiki markup links like [[Name]] or [[Name|Display]]."""
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"'''?([^']+)'''?", r"\1", text)
    return text.strip()


def fetch_wikitext() -> str:
    LOGGER.info("Fetching Pokédex wikitext from Infinite Fusion wiki...")
    data = get_json(WIKI_API, params={
        "action": "parse",
        "page": "Pokédex",
        "prop": "wikitext",
        "format": "json",
    })
    if not data:
        raise RuntimeError("Failed to fetch Pokédex page from wiki")
    return data["parse"]["wikitext"]["*"]


def parse_entries(wikitext: str) -> list[dict]:
    entries = []
    seen_ids: set[int] = set()

    for match in ENTRY_RE.finditer(wikitext):
        index    = int(match.group("index"))
        if_id    = int(match.group("id"))
        name     = clean_wikitext(match.group("name"))
        type1    = clean_wikitext(match.group("type1")).lower() or None
        type2    = clean_wikitext(match.group("type2")).lower() or None
        location = clean_wikitext(match.group("location"))
        notes    = clean_wikitext(match.group("notes") or "")

        if if_id in seen_ids:
            continue
        seen_ids.add(if_id)

        if not name or name.startswith("{{"):
            continue

        is_hoenn_only = bool(HOENN_ONLY_RE.search(notes) or HOENN_ONLY_RE.search(location))

        entries.append({
            "if_id":        if_id,
            "index":        index,
            "name_en":      name,
            "type1":        type1,
            "type2":        type2 if type2 else None,
            "generation":   detect_generation(index),
            "location_raw": location,
            "is_hoenn_only": is_hoenn_only,
        })

    LOGGER.info("Parsed %d Pokémon entries", len(entries))
    return sorted(entries, key=lambda e: e["if_id"])


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wikitext = fetch_wikitext()
    entries  = parse_entries(wikitext)

    OUTPUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2))
    LOGGER.info("Saved %d entries → %s", len(entries), OUTPUT)


if __name__ == "__main__":
    main()
