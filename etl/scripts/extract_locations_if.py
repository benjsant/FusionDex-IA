"""
ETL Step 5 — Extract Pokémon locations from Infinite Fusion wiki.

Sources (MediaWiki API):
  - Pokédex page (column "location_raw" already in pokedex_if.json) — parsed here
  - List of Static Encounters
  - List of Gift Pokémon and Trades

Output: data/locations_if.json
Format:
  [
    {
      "pokemon_name": str,
      "locations": [
        {"name": str, "region": str, "method": str, "notes": str}
      ]
    }
  ]
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from etl.utils.http import get_json

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

WIKI_API         = "https://infinitefusion.fandom.com/api.php"
INPUT_POKEDEX    = Path("data/pokedex_if.json")
OUTPUT           = Path("data/locations_if.json")

# Region keywords for auto-detection
KANTO_RE = re.compile(
    r"route [1-2]\d|viridian|pewter|cerulean|vermilion|lavender|celadon|"
    r"fuchsia|saffron|cinnabar|pallet|safari zone|victory road|mt\. moon|"
    r"rock tunnel|power plant|seafoam|pokemon tower|silph",
    re.IGNORECASE,
)
JOHTO_RE = re.compile(
    r"route [2-4]\d|new bark|cherrygrove|violet|azalea|goldenrod|ecruteak|"
    r"olivine|cianwood|mahogany|blackthorn|mount mortar|ice path|"
    r"dark cave|bell tower|burned tower|slowpoke well|ilex forest|"
    r"national park|mt\. silver|lake of rage",
    re.IGNORECASE,
)


def detect_region(location: str) -> str:
    if KANTO_RE.search(location):
        return "Kanto"
    if JOHTO_RE.search(location):
        return "Johto"
    return "Other"


def clean(text: str) -> str:
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"'''?([^']+)'''?", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def fetch_wikitext(page: str) -> str:
    data = get_json(WIKI_API, params={
        "action": "parse",
        "page": page,
        "prop": "wikitext",
        "format": "json",
    })
    if not data:
        raise RuntimeError(f"Failed to fetch wiki page: {page}")
    return data["parse"]["wikitext"]["*"]


# ─── Parse location_raw from Pokédex entries ─────────────────────────────────

def parse_pokedex_locations(entries: list[dict]) -> dict[str, list[dict]]:
    """
    Parse the raw location strings already extracted in pokedex_if.json.
    Returns a dict: pokemon_name → [location_record, ...]
    """
    result: dict[str, list[dict]] = {}

    for entry in entries:
        name     = entry["name_en"]
        location = entry.get("location_raw", "").strip()
        if not location:
            continue

        # Multiple locations separated by comma or newline
        parts = re.split(r",|\n|;", location)
        locs  = []
        for part in parts:
            part = clean(part)
            if not part:
                continue
            locs.append({
                "name":   part,
                "region": detect_region(part),
                "method": "wild",
                "notes":  "",
            })

        if locs:
            result[name] = locs

    return result


# ─── Parse static encounters ─────────────────────────────────────────────────

STATIC_ROW_RE = re.compile(
    r"\|-\s*\n"
    r"\s*\|\s*(?:\[\[(?:[^\]|]*\|)?)?(?P<pokemon>[^\|\]\n]+?)(?:\]\])?\s*\n"
    r"\s*\|\s*(?P<location>[^\|\n]+?)\s*\n"
    r"(?:\s*\|\s*(?P<notes>[^\|\n]*))?"
    , re.MULTILINE,
)


def parse_static_encounters(wikitext: str) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}

    for m in STATIC_ROW_RE.finditer(wikitext):
        pokemon  = clean(m.group("pokemon"))
        location = clean(m.group("location"))
        notes    = clean(m.group("notes") or "")

        if not pokemon or not location:
            continue

        entry = {
            "name":   location,
            "region": detect_region(location),
            "method": "static",
            "notes":  notes,
        }
        result.setdefault(pokemon, []).append(entry)

    return result


# ─── Merge and output ─────────────────────────────────────────────────────────

def merge(
    pokedex_locs: dict[str, list[dict]],
    static_locs: dict[str, list[dict]],
) -> list[dict]:
    all_names = set(pokedex_locs) | set(static_locs)
    output    = []

    for name in sorted(all_names):
        locations = []
        seen      = set()

        for loc in pokedex_locs.get(name, []) + static_locs.get(name, []):
            key = f"{loc['name']}|{loc['method']}"
            if key not in seen:
                seen.add(key)
                locations.append(loc)

        output.append({"pokemon_name": name, "locations": locations})

    return output


def main() -> None:
    if not INPUT_POKEDEX.exists():
        raise FileNotFoundError(f"{INPUT_POKEDEX} not found — run extract_pokedex_if.py first")

    entries = json.loads(INPUT_POKEDEX.read_text())

    LOGGER.info("Parsing locations from Pokédex entries...")
    pokedex_locs = parse_pokedex_locations(entries)

    LOGGER.info("Fetching static encounters from wiki...")
    static_wikitext = fetch_wikitext("List of Static Encounters")
    static_locs     = parse_static_encounters(static_wikitext)

    merged = merge(pokedex_locs, static_locs)

    OUTPUT.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    LOGGER.info("Saved locations for %d Pokémon → %s", len(merged), OUTPUT)


if __name__ == "__main__":
    main()
