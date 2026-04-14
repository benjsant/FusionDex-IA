"""
ETL — Extract Triple Fusions from the Infinite Fusion wiki.

Source : https://infinitefusion.fandom.com/wiki/Triple_Fusions
Output : data/triple_fusions_if.json

Each triple fusion is a post-game fusion of 3 legendaries or 3 fully-evolved
starters from the same region.  23 exist at the time of writing:
  - 8 legendary trios (Zapmolcuno, Enraicune, Kyodonquaza, Paldiatina,
                       Zekyushiram, Celemewchi, Deosectwo, Regiregi)
  - 15 starter trios   (5 regions × 3 evolution stages)

Structure per entry:
  {
    "name_en":        "Zapmolcuno",
    "components":     ["Articuno", "Moltres", "Zapdos"],
    "type":           "[Ice/Fire/Electric]/Flying",
    "stats":          {"hp":90, "attack":92, "defense":92,
                       "sp_attack":115, "sp_defense":100, "speed":92},
    "abilities": [
        {"name": "Serene Grace", "is_hidden": false},
        {"name": "Pressure",     "is_hidden": true},
    ],
    "steps_to_hatch": 20655,
    "evolves_from":   null,
    "evolution_level": null,
  }
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from etl.utils.http import get_json

from etl.utils.logging import setup_logging

LOGGER = setup_logging(__name__)

WIKI_API = "https://infinitefusion.fandom.com/api.php"
OUTPUT   = Path("data/triple_fusions_if.json")


def fetch_wikitext(page: str) -> str:
    data = get_json(WIKI_API, params={
        "action": "parse",
        "page":   page,
        "prop":   "wikitext",
        "format": "json",
    })
    if not data:
        raise RuntimeError(f"Failed to fetch wiki page: {page}")
    return data["parse"]["wikitext"]["*"]


def parse_block(name: str, block: str) -> dict | None:
    # Cut at next level-2 header if we captured too much
    block = re.split(r"^==[^=]", block, flags=re.MULTILINE)[0]

    # ── Components ───────────────────────────────────────────────────────────
    comp_match = re.search(r"!\s*Base Pok[eé]mon\s*\n(.*?)(?=\n\|-)", block, re.DOTALL)
    components: list[str] = []
    if comp_match:
        text = comp_match.group(1)
        for cell in re.findall(
            r"\|(?:\s*colspan=\"\d+\"\s*\|)?\s*([A-Za-z][A-Za-z\s\.\-]*)",
            text,
        ):
            c = cell.strip()
            if c and c not in ("HP", "ATK", "DEF", "SPE", "BST"):
                components.append(c)
    components = components[:3]

    if len(components) != 3:
        LOGGER.warning("%s: expected 3 components, got %d", name, len(components))
        return None

    # ── Stats : find 7 consecutive `|NNN` lines whose 7th equals sum of 6 ────
    stats_dict: dict[str, int] | None = None
    for sm in re.finditer(
        r"\|\s*(\d{1,3})\s*\n\|\s*(\d{1,3})\s*\n\|\s*(\d{1,3})\s*\n"
        r"\|\s*(\d{1,3})\s*\n\|\s*(\d{1,3})\s*\n\|\s*(\d{1,3})\s*\n\|\s*(\d{1,3})",
        block,
    ):
        nums = list(map(int, sm.groups()))
        if nums[-1] == sum(nums[:-1]):
            stats_dict = {
                "hp":         nums[0],
                "attack":     nums[1],
                "defense":    nums[2],
                "sp_attack":  nums[3],
                "sp_defense": nums[4],
                "speed":      nums[5],
            }
            break

    if stats_dict is None:
        LOGGER.warning("%s: no stats parsed", name)
        return None

    # ── Type (may be bracketed custom combo) ─────────────────────────────────
    type_str: str | None = None
    tm = re.search(r"!\s*Type\s*\n.*?>([A-Za-z\[\]/]+)<", block, re.DOTALL)
    if tm:
        type_str = tm.group(1).strip()
    else:
        tm2 = re.search(r"!\s*Type\s*\n\|[^\n]*?\|\s*([A-Za-z\[\]/ ]+)", block)
        if tm2:
            type_str = tm2.group(1).strip()

    # ── Abilities : 1 to 3 entries, some flagged "- HA" (hidden ability) ────
    abilities: list[dict] = []
    am = re.search(r"!\s*Abilities\s*\n(.*?)(?=\n!|\n\|-)", block, re.DOTALL)
    if am:
        ab_text = am.group(1)
        # Each ability is a cell; may contain " - HA" suffix
        for cell in re.findall(
            r"\|(?:\s*colspan=\"\d+\"\s*\|)?\s*([A-Za-z][A-Za-z\s\-]*?)\s*(?=\n|\||$)",
            ab_text,
        ):
            c = cell.strip()
            if not c or c == "-":
                continue
            is_hidden = c.endswith("- HA") or c.endswith("-HA")
            name_clean = re.sub(r"\s*-\s*HA\s*$", "", c).strip()
            if not name_clean or name_clean == "HA":
                continue
            abilities.append({"name": name_clean, "is_hidden": is_hidden})

    # ── Steps to hatch ───────────────────────────────────────────────────────
    sh = re.search(r"Steps To Hatch[^\n]*\n\|[^|\n]*\|\s*(\d+)", block)
    steps = int(sh.group(1)) if sh else None

    # ── Evolution chain ──────────────────────────────────────────────────────
    ev = re.search(r"'''Evolve\s+(\w+)\s+at\s+Lv\.\s*(\d+)'''", block)
    evolves_from, evo_level = (ev.group(1), int(ev.group(2))) if ev else (None, None)

    return {
        "name_en":         name,
        "components":      components,
        "type":            type_str,
        "stats":           stats_dict,
        "abilities":       abilities,
        "steps_to_hatch":  steps,
        "evolves_from":    evolves_from,
        "evolution_level": evo_level,
    }


def parse_triple_fusions(wikitext: str) -> list[dict]:
    parts = re.split(r"^===\s*([^=]+?)\s*===\s*$", wikitext, flags=re.MULTILINE)
    results: list[dict] = []
    for i in range(1, len(parts), 2):
        name  = parts[i].strip()
        block = parts[i + 1] if i + 1 < len(parts) else ""
        parsed = parse_block(name, block)
        if parsed:
            results.append(parsed)
    return results


def main() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)
    LOGGER.info("Fetching Triple_Fusions from IF wiki...")
    wikitext = fetch_wikitext("Triple_Fusions")
    fusions  = parse_triple_fusions(wikitext)
    OUTPUT.write_text(json.dumps(fusions, ensure_ascii=False, indent=2))
    LOGGER.info("Saved %d triple fusions → %s", len(fusions), OUTPUT)


if __name__ == "__main__":
    main()
