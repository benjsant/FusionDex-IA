"""
ETL Step 4 — Extract abilities from the Infinite Fusion wiki.

Source: wiki IF "List of Abilities"
  - Ability name (EN)
  - Description (EN)
  - List of Pokémon that have this ability (hidden = bold-italic)

Output: data/abilities_if.json
"""

from __future__ import annotations

import re
from pathlib import Path

from etl.utils.io import save_json
from etl.utils.logging import setup_logging
from etl.utils.wikitext import clean_wikitext, fetch_wikitext

LOGGER = setup_logging(__name__)

OUTPUT = Path("data/abilities_if.json")

HIDDEN_RE   = re.compile(r"'''''\s*(.+?)\s*'''''")
BULLET_RE   = re.compile(r"^\*\s*(.+)$", re.MULTILINE)

clean = clean_wikitext


def parse_pokemon_block(block: str) -> list[dict]:
    pokemon_list: list[dict] = []
    seen: set[str] = set()

    for m in HIDDEN_RE.finditer(block):
        name = clean(m.group(1))
        if name and name not in seen:
            seen.add(name)
            pokemon_list.append({"name": name, "is_hidden": True})

    cleaned = HIDDEN_RE.sub("", block)
    for m in BULLET_RE.finditer(cleaned):
        name = clean(m.group(1))
        if name and name not in seen:
            seen.add(name)
            pokemon_list.append({"name": name, "is_hidden": False})

    return pokemon_list


def parse_abilities(wikitext: str) -> list[dict]:
    abilities: list[dict] = []
    seen: set[str] = set()

    # Split on row separators
    rows = re.split(r"\n\|-", wikitext)

    for row in rows:
        lines = row.strip().splitlines()
        # Collect pipe-started cells (skip style attributes merged with content)
        cells: list[str] = []
        current_cell_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and not stripped.startswith("|-") and not stripped.startswith("|+"):
                if current_cell_lines:
                    cells.append("\n".join(current_cell_lines))
                current_cell_lines = [stripped]
            elif current_cell_lines:
                current_cell_lines.append(stripped)

        if current_cell_lines:
            cells.append("\n".join(current_cell_lines))

        if len(cells) < 2:
            continue

        # Cell 0: ability name — may be `|[[bulbapedia:Name_(Ability)|Name]]`
        name_raw = cells[0].lstrip("|").strip()
        # Handle `| style="..." | content` in same cell
        if "|" in name_raw and 'style=' in name_raw:
            name_raw = name_raw.split("|", 1)[-1].strip()
        name = clean(name_raw)
        if not name or name in seen or name.startswith("!"):
            continue
        seen.add(name)

        # Cell 1: description
        desc_raw = cells[1].lstrip("|").strip()
        if "|" in desc_raw and 'style=' in desc_raw:
            desc_raw = desc_raw.split("|", 1)[-1].strip()
        description = clean(desc_raw)

        # Cell 2+: pokemon block (may span multiple lines / sub-cells)
        pokemon_block = "\n".join(cells[2:]) if len(cells) > 2 else ""
        # Also include trailing lines of cell 1 if pokemon list is embedded
        pokemon_list = parse_pokemon_block(pokemon_block)

        abilities.append({
            "name_en":        name,
            "name_fr":        None,
            "description_en": description,
            "description_fr": None,
            "pokemon":        pokemon_list,
        })

    LOGGER.info("Parsed %d abilities", len(abilities))
    return abilities


def main() -> None:
    LOGGER.info("Fetching List of Abilities from wiki...")
    wikitext  = fetch_wikitext("List of Abilities")
    abilities = parse_abilities(wikitext)

    save_json(OUTPUT, abilities)
    LOGGER.info("Saved %d abilities → %s", len(abilities), OUTPUT)


if __name__ == "__main__":
    main()
