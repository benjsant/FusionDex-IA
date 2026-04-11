"""
ETL Step 3b — Enrich moves with French names from PokeAPI.

Pour chaque move dans moves_if.json, interroge PokeAPI /move/{slug}
pour récupérer le nom FR.
Slug = name_en.lower().replace(" ", "-"), ex: "Bug Bite" → "bug-bite"

Met à jour moves_if.json sur place avec name_fr renseigné.
Idempotent : saute les moves ayant déjà un name_fr.

Output: data/moves_if.json (modifié in-place avec name_fr)
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

POKEAPI_MOVE  = "https://pokeapi.co/api/v2/move/{}"
MOVES_FILE    = Path("data/moves_if.json")
MAX_WORKERS   = 4
REQUEST_DELAY = 0.05   # secondes par worker

# Priorité de version pour la description FR — on prend la plus récente disponible
VERSION_PRIO = [
    "ultra-sun-ultra-moon", "sun-moon", "omega-ruby-alpha-sapphire", "x-y",
    "black-2-white-2", "black-white",
    "lets-go-pikachu-lets-go-eevee", "sword-shield",  # fallback Gen 8+ moves
]

# Corrections manuelles : nom IF wiki → slug PokeAPI exact
MANUAL_SLUGS: dict[str, str] = {
    "Smelling Salts":      "smelling-salts",
    "Vice Grip":           "vice-grip",
    "SolarBeam":           "solar-beam",
    "SonicBoom":           "sonic-boom",
    "ThunderPunch":        "thunder-punch",
    "ThunderShock":        "thunder-shock",
    "FirePunch":           "fire-punch",
    "IcePunch":            "ice-punch",
    "ExtremeSpeed":        "extreme-speed",
    "DynamicPunch":        "dynamic-punch",
    "DoubleSlap":          "double-slap",
    "Softboiled":          "soft-boiled",
    "PoisonPowder":        "poison-powder",
    "PinMissile":          "pin-missile",
    "TwinNeedle":          "twineedle",
    "Hi Jump Kick":        "high-jump-kick",
    "Smokescreen":         "smokescreen",
    "Sand-Attack":         "sand-attack",
    "Growl":               "growl",
    "Tail Whip":           "tail-whip",
}


def to_slug(name_en: str) -> str:
    """Convert move name to PokeAPI slug."""
    if name_en in MANUAL_SLUGS:
        return MANUAL_SLUGS[name_en]
    return name_en.lower().replace(" ", "-").replace("'", "").replace(".", "")


def _enrich_one(move: dict) -> tuple[dict, str | None, str | None]:
    slug = to_slug(move["name_en"])
    name_fr, desc_fr = fetch_fr_translation(
        POKEAPI_MOVE.format(slug), VERSION_PRIO, logger=LOGGER,
    )
    sleep_between_requests(REQUEST_DELAY)
    return move, name_fr, desc_fr


def main() -> None:
    if not MOVES_FILE.exists():
        raise FileNotFoundError("data/moves_if.json not found — run extract_moves_if.py first")

    moves = json.loads(MOVES_FILE.read_text())
    to_enrich = [m for m in moves if not m.get("name_fr") or not m.get("description_fr")]
    LOGGER.info("%d moves à enrichir en FR (sur %d)", len(to_enrich), len(moves))

    def save() -> None:
        MOVES_FILE.write_text(json.dumps(moves, ensure_ascii=False, indent=2))

    found, not_found = enrich_items_parallel(
        to_enrich,
        _enrich_one,
        save=save,
        logger=LOGGER,
        save_every=100,
        max_workers=MAX_WORKERS,
        label="moves",
    )

    LOGGER.info("Terminé — %d FR trouvés | %d non trouvés", found, len(not_found))

    missing = [m["name_en"] for m in moves if not m.get("name_fr")]
    if missing:
        LOGGER.warning("%d moves sans nom FR : %s", len(missing), missing[:20])


if __name__ == "__main__":
    main()
