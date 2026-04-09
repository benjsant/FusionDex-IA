"""
ETL Step 7 — Merge base movesets (Pokepedia) with IF-specific overrides.

Rules:
  A) Move learned in base game (Pokepedia) → source='base', keep as-is
  B) Move taught by a CT in IF that wasn't in base → add row, source='infinite_fusion'
  C) Move already known by another method in base, but IF adds a CT for it
     → keep both rows (different method = different row, UNIQUE constraint is on
       (pokemon_id, move_id, method))
  D) Move taught by a tutor in IF that wasn't in base → add row, source='infinite_fusion'

The merge works on move names (FR) as the join key.
A name normalisation step handles apostrophe variants and case differences.

Input:
  data/movesets_base.json   — from Pokepedia scraper
  data/tms_if.json          — TMs from IF wiki (move_name EN)
  data/tutors_if.json       — Tutors from IF wiki (move_name EN)
  data/moves_if.json        — Master move list with name_en + name_fr

Output:
  data/movesets_merged.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

IN_MOVESETS = Path("data/movesets_base.json")
IN_TMS      = Path("data/tms_if.json")
IN_TUTORS   = Path("data/tutors_if.json")
IN_MOVES    = Path("data/moves_if.json")
OUTPUT      = Path("data/movesets_merged.json")


def normalize(name: str) -> str:
    """Normalize move name for fuzzy matching."""
    return (
        name.lower()
        .replace("'", "'")
        .replace("'", "'")
        .replace("-", " ")
        .strip()
    )


def build_name_fr_to_en(moves: list[dict]) -> dict[str, str]:
    """Build a mapping: normalized_name_fr → name_en."""
    mapping: dict[str, str] = {}
    for m in moves:
        if m.get("name_fr"):
            mapping[normalize(m["name_fr"])] = m["name_en"]
    return mapping


def build_name_en_to_fr(moves: list[dict]) -> dict[str, str]:
    """Build a mapping: normalized_name_en → name_fr."""
    mapping: dict[str, str] = {}
    for m in moves:
        if m.get("name_fr"):
            mapping[normalize(m["name_en"])] = m["name_fr"]
    return mapping


def main() -> None:
    for f in (IN_MOVESETS, IN_TMS, IN_TUTORS, IN_MOVES):
        if not f.exists():
            raise FileNotFoundError(f"{f} not found — run prior ETL steps first")

    base_movesets : list[dict] = json.loads(IN_MOVESETS.read_text())
    tms_if        : list[dict] = json.loads(IN_TMS.read_text())
    tutors_if     : list[dict] = json.loads(IN_TUTORS.read_text())
    moves_if      : list[dict] = json.loads(IN_MOVES.read_text())

    en_to_fr = build_name_en_to_fr(moves_if)
    fr_to_en = build_name_fr_to_en(moves_if)

    # ── Index base movesets by (if_id, move_name_fr_normalized, method) ──────
    base_index: set[tuple[int, str, str]] = set()
    merged: list[dict] = []

    for record in base_movesets:
        key = (record["pokemon_if_id"], normalize(record["move_name_fr"]), record["method"])
        base_index.add(key)
        merged.append(record)

    # ── TMs IF — add CT rows not already present ──────────────────────────────
    # tms_if entries have move_name in EN; we convert to FR for consistency
    # then check if (pokemon_id, move_name_fr, 'tm') already exists in base

    # Build set of (if_id, move_name_fr_norm) already known via any method
    base_any_method: set[tuple[int, str]] = {
        (r["pokemon_if_id"], normalize(r["move_name_fr"]))
        for r in base_movesets
    }

    # tms_if only lists the move + location, not which Pokémon learn it.
    # The Pokémon→CT assignment comes from the base moveset (method='tm').
    # What we add here are CT rows for moves that IF introduces as NEW CTs
    # (i.e., the Pokémon learned the move by another method in base, but
    # IF also makes it available as a CT).
    #
    # To do that properly we'd need the "which Pokémon can use this CT" list
    # from IF — which isn't in the wiki directly.
    # Strategy: flag these CTs as IF-specific; the CT-to-Pokémon assignment
    # will be handled manually or via a future data source.
    # For now we record IF-only TM move names for reference.

    if_tm_names_fr: set[str] = set()
    for tm in tms_if:
        name_fr = en_to_fr.get(normalize(tm["move_name"]))
        if name_fr:
            if_tm_names_fr.add(normalize(name_fr))

    LOGGER.info("IF TMs mapped to FR names: %d", len(if_tm_names_fr))

    # ── Tutors IF — same logic ────────────────────────────────────────────────
    if_tutor_names_fr: set[str] = set()
    for tutor in tutors_if:
        name_fr = en_to_fr.get(normalize(tutor["move_name"]))
        if name_fr:
            if_tutor_names_fr.add(normalize(name_fr))

    LOGGER.info("IF Tutors mapped to FR names: %d", len(if_tutor_names_fr))

    # ── Flag existing base records that are also IF TMs or tutors ────────────
    # Update source for moves that are ALSO available via IF-specific methods
    override_count = 0
    for record in merged:
        norm = normalize(record["move_name_fr"])
        if record["method"] == "tm" and norm in if_tm_names_fr:
            # Already a TM in base AND in IF — mark as both
            record["also_if_tm"] = True
        if record["method"] == "tutor" and norm in if_tutor_names_fr:
            record["also_if_tutor"] = True

    # ── Add IF-only methods for base Pokémon ─────────────────────────────────
    # For each base Pokémon that learns a move by some method, if IF
    # adds a NEW method (tm/tutor) not present in base, add a row.
    # We derive this from the CT/tutor lists cross-referenced with base records.

    base_pokemon_ids = {r["pokemon_if_id"] for r in base_movesets}

    for record in base_movesets:
        if_id   = record["pokemon_if_id"]
        norm    = normalize(record["move_name_fr"])

        # If this move is in IF TM list AND the Pokémon doesn't already
        # have it via 'tm' method in base → add an IF-specific tm row
        if norm in if_tm_names_fr:
            tm_key = (if_id, norm, "tm")
            if tm_key not in base_index:
                base_index.add(tm_key)
                merged.append({
                    "pokemon_if_id": if_id,
                    "move_name_fr":  record["move_name_fr"],
                    "method":        "tm",
                    "level":         None,
                    "source":        "infinite_fusion",
                })
                override_count += 1

        # Same for tutors
        if norm in if_tutor_names_fr:
            tutor_key = (if_id, norm, "tutor")
            if tutor_key not in base_index:
                base_index.add(tutor_key)
                merged.append({
                    "pokemon_if_id": if_id,
                    "move_name_fr":  record["move_name_fr"],
                    "method":        "tutor",
                    "level":         None,
                    "source":        "infinite_fusion",
                })
                override_count += 1

    merged.sort(key=lambda r: (r["pokemon_if_id"], r["method"], r.get("level") or 0))

    OUTPUT.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    LOGGER.info(
        "Merged %d records (%d base + %d IF overrides) → %s",
        len(merged), len(base_movesets), override_count, OUTPUT,
    )


if __name__ == "__main__":
    main()
