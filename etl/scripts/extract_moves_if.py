"""
ETL Step 3 — Extract moves, TMs and tutors from the Infinite Fusion wiki.

Sources (MediaWiki API):
  - List_of_Moves  → moves EN: name, type, category, power, accuracy, PP, description
  - List_of_TMs    → CTs: number, move name, location in IF
  - List_of_Tutors → tutor moves: name, location, price

Noms FR : renseignés plus tard via Pokepedia (movesets_base.json contient name_fr).
          load_db.py fait la jointure move.name_en ↔ moveset.move_name_fr via
          un mapping inversé construit depuis les movesets.

Output: data/moves_if.json, data/tms_if.json, data/tutors_if.json
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from etl.utils.http import get_json

LOGGER   = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

WIKI_API   = "https://infinitefusion.fandom.com/api.php"
OUT_MOVES  = Path("data/moves_if.json")
OUT_TMS    = Path("data/tms_if.json")
OUT_TUTORS = Path("data/tutors_if.json")

# Section headers: ==Bug-type== or ==Bug-type moves==
TYPE_HEADER_RE = re.compile(r"^==\s*([A-Za-z]+(?:/[A-Za-z]+)?)-type(?:\s+moves)?\s*==$", re.MULTILINE)

# Row separator
ROW_SEP_RE = re.compile(r"^\|-", re.MULTILINE)

# data-sort-value="Attack Order" | [[...|Attack Order]]  OR  | Attack Order
CELL_NAME_RE  = re.compile(r'data-sort-value="([^"]+)"')
WIKILINK_RE   = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
SORTVAL_RE    = re.compile(r'data-sort-value="([^"]*)"')


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


def clean(text: str) -> str:
    """Strip wikitext markup and HTML tags."""
    text = WIKILINK_RE.sub(r"\1", text)
    text = re.sub(r"'''?([^']+)'''?", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    return text.strip()


def parse_cell(raw: str) -> str:
    """Extract display value from a wiki table cell (handles data-sort-value)."""
    raw = raw.strip().lstrip("|").strip()
    # data-sort-value="90" | 90  → take the bare value after |
    if "|" in raw:
        raw = raw.split("|", 1)[-1].strip()
    return clean(raw)


def parse_int_or_none(value: str) -> int | None:
    v = parse_cell(value).strip("-— %")
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


# ─── Moves ────────────────────────────────────────────────────────────────────

def extract_moves(wikitext: str) -> list[dict]:
    """
    Parse ==Type-type== sections, each containing a wikitable of moves.
    Columns: Move | Category | Power | Accuracy | PP | Description
    """
    moves: list[dict] = []
    seen: set[str]    = set()

    # Split on type headers
    parts = TYPE_HEADER_RE.split(wikitext)
    # parts[0] = preamble, then alternating: type_name, content_block, ...

    for i in range(1, len(parts), 2):
        type_en      = parts[i].capitalize()
        block        = parts[i + 1] if i + 1 < len(parts) else ""

        # Split block into rows on "|-"
        rows = ROW_SEP_RE.split(block)

        for row in rows[1:]:   # skip table header
            lines = [l.strip() for l in row.strip().splitlines() if l.strip()]
            # Filter out header lines (starting with !) and row attributes
            cells = [l for l in lines if l.startswith("|") and not l.startswith("|-")]

            if len(cells) < 6:
                continue

            # Cell 0 : move name
            # May be:  | data-sort-value="Bug Bite" | [[bulbapedia:...|Bug Bite]]
            # Or:      | [[...|Bug Bite]]
            name_cell = cells[0].lstrip("|").strip()
            # Try data-sort-value first (most reliable)
            m = SORTVAL_RE.search(name_cell)
            if m:
                name = m.group(1).strip()
            else:
                name = clean(name_cell)

            if not name or name.startswith("{") or not name[0].isalpha():
                continue

            if name in seen:
                continue
            seen.add(name)

            category    = parse_cell(cells[1]).capitalize()
            power       = parse_int_or_none(cells[2])
            accuracy    = parse_int_or_none(cells[3])
            pp          = parse_int_or_none(cells[4]) or 1
            description = parse_cell(cells[5]) if len(cells) > 5 else ""

            moves.append({
                "name_en":        name,
                "name_fr":        None,
                "type_en":        type_en,
                "category":       category if category in ("Physical", "Special", "Status") else "Status",
                "power":          power,
                "accuracy":       accuracy,
                "pp":             pp,
                "description_en": description,
                "description_fr": None,
                "source":         "base",
            })

    LOGGER.info("Parsed %d moves", len(moves))
    return moves


# ─── TMs ──────────────────────────────────────────────────────────────────────

# | TM01 | [[bulbapedia:...|Work Up]] | Location
TM_ROW_RE = re.compile(
    r"\|\s*TM(?P<number>\d+)\s*\|[^\|]*?\|\s*"
    r"(?:data-sort-value=\"[^\"]*\"\s*\|)?\s*"
    r"(?:\[\[(?:[^\]|]*\|)?)?(?P<move>[A-Za-z][^\|\]\n]{1,40})(?:\]\])?\s*\|"
    r"\s*(?P<location>[^\|\n]+)",
    re.IGNORECASE,
)

def extract_tms(wikitext: str) -> list[dict]:
    tms: list[dict] = []
    seen: set[int]  = set()

    for m in TM_ROW_RE.finditer(wikitext):
        number = int(m.group("number"))
        if number in seen:
            continue
        seen.add(number)
        tms.append({
            "number":    number,
            "move_name": clean(m.group("move")),
            "location":  clean(m.group("location")),
        })

    tms.sort(key=lambda x: x["number"])
    LOGGER.info("Parsed %d TMs", len(tms))
    return tms


# ─── Tutors ───────────────────────────────────────────────────────────────────

TUTOR_ROW_RE = re.compile(
    r"\|-[^\n]*\n"
    r"\s*\|\s*(?:data-sort-value=\"[^\"]*\"\s*\|\s*)?"
    r"(?:\[\[(?:[^\]|]*\|)?)?(?P<name>[A-Za-z][^\|\]\n]{1,40})(?:\]\])?\s*\n"
    r"\s*\|\s*(?P<location>[^\|\n]+)",
    re.MULTILINE,
)

def extract_tutors(wikitext: str) -> list[dict]:
    tutors: list[dict] = []
    seen: set[str]     = set()

    for m in TUTOR_ROW_RE.finditer(wikitext):
        name = clean(m.group("name"))
        if not name or name in seen:
            continue
        seen.add(name)
        tutors.append({
            "move_name": name,
            "location":  clean(m.group("location")),
        })

    LOGGER.info("Parsed %d tutor moves", len(tutors))
    return tutors


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)

    LOGGER.info("Fetching List of Moves from IF wiki...")
    moves = extract_moves(fetch_wikitext("List_of_Moves"))
    OUT_MOVES.write_text(json.dumps(moves, ensure_ascii=False, indent=2))
    LOGGER.info("Saved %d moves → %s", len(moves), OUT_MOVES)

    LOGGER.info("Fetching List of TMs from IF wiki...")
    tms = extract_tms(fetch_wikitext("List_of_TMs"))
    OUT_TMS.write_text(json.dumps(tms, ensure_ascii=False, indent=2))
    LOGGER.info("Saved %d TMs → %s", len(tms), OUT_TMS)

    LOGGER.info("Fetching List of Tutors from IF wiki...")
    try:
        tutors = extract_tutors(fetch_wikitext("List_of_Move_Tutors"))
    except Exception:
        tutors = []
        LOGGER.warning("List of Tutors non disponible — skipped")
    OUT_TUTORS.write_text(json.dumps(tutors, ensure_ascii=False, indent=2))
    LOGGER.info("Saved %d tutors → %s", len(tutors), OUT_TUTORS)


if __name__ == "__main__":
    main()
