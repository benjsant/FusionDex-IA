"""
ETL — Extract wild/static/legendary encounters from the Infinite Fusion wiki.

Sources:
  - https://infinitefusion.fandom.com/wiki/Wild_Encounters
  - https://infinitefusion.fandom.com/wiki/List_of_Static_Encounters
  - https://infinitefusion.fandom.com/wiki/Legendary_Pokémon

Output: data/encounters_if.json
Format per entry:
  {
    "national_id": int,
    "pokemon_name": str,
    "location_name": str,          # e.g. "Route 1"
    "location_if_id": int | null,  # internal IF map ID
    "method": str,                 # wild|fishing|static
    "level_min": int | null,
    "level_max": int | null,
    "encounter_rate": str | null,  # e.g. "50%" or "45%|45%|-" (morn|day|night)
    "notes": str | null,
  }

Excludes: Pokémon marked is_hoenn_only (national_id in 502–572 range, but
Wild_Encounters doesn't reference them anyway).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from etl.utils.http import get_json

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

WIKI_API = "https://infinitefusion.fandom.com/api.php"
OUTPUT   = Path("data/encounters_if.json")

# EncounterTable/Section → DB method
SECTION_TO_METHOD = {
    "Grass":       "wild",
    "Cave":        "wild",
    "Surf":        "wild",
    "Poké Radar":  "wild",
    "Rock Smash":  "wild",
    "Old Rod":     "fishing",
    "Good Rod":    "fishing",
    "Super Rod":   "fishing",
}

# Pokémon Hoenn-only (IF IDs 502–572, national IDs correspond to Gen3 starters etc.)
# Wild_Encounters doesn't include them but we filter just in case
HOENN_ONLY_NATIONAL = set(range(252, 387))  # not actually excluded from wild, just a safeguard


def fetch_wikitext(page: str) -> str:
    data = get_json(WIKI_API, params={
        "action": "parse", "page": page, "prop": "wikitext", "format": "json",
    })
    if not data or "parse" not in data:
        raise RuntimeError(f"Failed to fetch {page}")
    return data["parse"]["wikitext"]["*"]


def clean_wikilinks(text: str) -> str:
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"'''?([^']+)'''?", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


# ── Wild Encounters ───────────────────────────────────────────────────────────

LOCATION_RE = re.compile(r"'''(.+?) \(ID (\d+)\)'''")
ENCOUNTER_RE = re.compile(
    r"\{\{EncounterTable/Data\|"
    r"(\d+)\|"           # national_id
    r"([^|]+)\|"         # name_en
    r"([^|]+)\|"         # type1
    r"([^|]*)\|"         # type2
    r"([^|]+)\|"         # levels (e.g. "2-5")
    r"([^|]+)"           # catch_rate
    r"(?:\|([^}]*))?"    # optional rate columns
    r"\}\}"
)
SECTION_RE = re.compile(r"\{\{EncounterTable/Section\|([^}]+)\}\}")
ROCK_SMASH_RE = re.compile(
    r"\{\{EncounterTable/RockSmash\|(\d+)\|([^|]+)\|([^|]+)\|([^|]*)\|([^}]+)\}\}"
)


def parse_level_range(s: str) -> tuple[int | None, int | None]:
    s = s.strip()
    m = re.match(r"(\d+)-(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"(\d+)", s)
    if m:
        v = int(m.group(1))
        return v, v
    return None, None


def parse_wild_encounters(wikitext: str) -> list[dict]:
    entries: list[dict] = []
    current_location: str | None = None
    current_if_id:   int | None  = None
    current_method:  str         = "wild"

    for line in wikitext.splitlines():
        line = line.strip()

        # New location block
        loc_m = LOCATION_RE.search(line)
        if loc_m:
            current_location = loc_m.group(1).strip()
            current_if_id    = int(loc_m.group(2))
            current_method   = "wild"
            continue

        # Section (method)
        sec_m = SECTION_RE.search(line)
        if sec_m:
            current_method = SECTION_TO_METHOD.get(sec_m.group(1).strip(), "wild")
            continue

        # Rock Smash (separate template)
        rs_m = ROCK_SMASH_RE.search(line)
        if rs_m and current_location:
            nat_id = int(rs_m.group(1))
            name   = clean_wikilinks(rs_m.group(2))
            levels = rs_m.group(5).strip()
            lmin, lmax = parse_level_range(levels.split("|")[0])
            entries.append({
                "national_id":     nat_id,
                "pokemon_name":    name,
                "location_name":   current_location,
                "location_if_id":  current_if_id,
                "method":          "wild",
                "level_min":       lmin,
                "level_max":       lmax,
                "encounter_rate":  None,
                "notes":           "Rock Smash",
            })
            continue

        # Encounter data
        enc_m = ENCOUNTER_RE.search(line)
        if enc_m and current_location:
            nat_id    = int(enc_m.group(1))
            name      = clean_wikilinks(enc_m.group(2))
            levels    = enc_m.group(5).strip()
            rate_cols = enc_m.group(7) or ""

            lmin, lmax = parse_level_range(levels)

            # Rate columns: may be "50%|50%|-" (morn|day|night) or just "50%"
            rate_parts = [r.strip() for r in rate_cols.split("|") if r.strip()]
            enc_rate   = "|".join(rate_parts) if rate_parts else None

            # Strip small-tag notes from rate (e.g. "50% <small>(...)</small>")
            if enc_rate:
                enc_rate = re.sub(r"<small>[^<]*</small>", "", enc_rate).strip()

            entries.append({
                "national_id":    nat_id,
                "pokemon_name":   name,
                "location_name":  current_location,
                "location_if_id": current_if_id,
                "method":         current_method,
                "level_min":      lmin,
                "level_max":      lmax,
                "encounter_rate": enc_rate or None,
                "notes":          None,
            })

    return entries


# ── Static Encounters ─────────────────────────────────────────────────────────

STATIC_ROW_RE = re.compile(
    r"\|\s*(?:rowspan=\"\d+\"\s*\|\s*)?([A-Z][^|{}\n]+?)\s*\|\|"  # pokemon name
    r"\s*(?:\[\[)?([^\[\]|{}\n]+?)(?:\]\])?\s*\|\|"               # location
    r"\s*(?:rowspan=\"\d+\"\s*\|\s*)?(\d+)"                        # level
    r"(?:\s*\|\|?\s*([^\n]*))?",                                    # notes
    re.MULTILINE,
)


def parse_static_encounters(wikitext: str) -> list[dict]:
    entries: list[dict] = []
    seen: set[tuple] = set()

    # Skip the Legendaries section (handled separately)
    # Static page says "==Legendaries== See [[Legendary Pokémon]]"
    wikitext = re.split(r"==Non-legendaries", wikitext, maxsplit=1)[-1]

    for m in STATIC_ROW_RE.finditer(wikitext):
        name     = clean_wikilinks(m.group(1)).strip()
        location = clean_wikilinks(m.group(2)).strip()
        level    = int(m.group(3))
        notes    = clean_wikilinks(m.group(4) or "").strip() or None

        # Skip HTML-heavy notes rows and header rows
        if not name or not location or name.startswith("|") or "colspan" in name.lower():
            continue
        # Skip duplicates (rowspan rows)
        key = (name.lower(), location.lower())
        if key in seen:
            continue
        seen.add(key)

        entries.append({
            "national_id":    None,   # resolved later by name
            "pokemon_name":   name,
            "location_name":  location,
            "location_if_id": None,
            "method":         "static",
            "level_min":      level,
            "level_max":      level,
            "encounter_rate": None,
            "notes":          notes,
        })

    return entries


# ── Legendary Encounters ──────────────────────────────────────────────────────

LEGEND_SECTION_RE = re.compile(r"^=== ?([^=\n]+?) ?===\s*$", re.MULTILINE)
LEGEND_LOCATION_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")


def parse_legendary_encounters(wikitext: str) -> list[dict]:
    entries: list[dict] = []
    seen: set[str] = set()

    # Split on === sections
    parts = LEGEND_SECTION_RE.split(wikitext)
    # parts: [preamble, name1, content1, name2, content2, ...]

    for i in range(1, len(parts), 2):
        name    = parts[i].strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""

        # Skip meta-sections
        if name in ("Defeating the Elite Four Pokémon Champion", "Clearing Mt. Silver",
                    "Respawning Legendaries"):
            continue

        # Find first wikilink as location
        loc_m = LEGEND_LOCATION_RE.search(content)
        location = clean_wikilinks(loc_m.group(1)) if loc_m else "Unknown"

        # Level: look for "Lv." or "level" or a number near the pokemon name
        lv_m = re.search(r"[Ll]v\.?\s*(\d+)|[Ll]evel\s*(\d+)", content)
        level = int(lv_m.group(1) or lv_m.group(2)) if lv_m else None

        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        entries.append({
            "national_id":    None,
            "pokemon_name":   name,
            "location_name":  location,
            "location_if_id": None,
            "method":         "static",
            "level_min":      level,
            "level_max":      level,
            "encounter_rate": None,
            "notes":          "Legendary",
        })

    return entries


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)

    LOGGER.info("Fetching Wild_Encounters...")
    wild_wt  = fetch_wikitext("Wild_Encounters")
    wild     = parse_wild_encounters(wild_wt)
    LOGGER.info("  → %d wild encounter entries", len(wild))

    LOGGER.info("Fetching List_of_Static_Encounters...")
    static_wt = fetch_wikitext("List_of_Static_Encounters")
    static    = parse_static_encounters(static_wt)
    LOGGER.info("  → %d static encounter entries", len(static))

    LOGGER.info("Fetching Legendary_Pokémon...")
    legend_wt = fetch_wikitext("Legendary_Pokémon")
    legendaries = parse_legendary_encounters(legend_wt)
    LOGGER.info("  → %d legendary encounter entries", len(legendaries))

    all_entries = wild + static + legendaries
    LOGGER.info("Total: %d encounter entries", len(all_entries))

    OUTPUT.write_text(json.dumps(all_entries, ensure_ascii=False, indent=2))
    LOGGER.info("Saved → %s", OUTPUT)


if __name__ == "__main__":
    main()
