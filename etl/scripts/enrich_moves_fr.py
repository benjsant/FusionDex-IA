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
import logging
import time
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

POKEAPI_MOVE  = "https://pokeapi.co/api/v2/move/{}"
MOVES_FILE    = Path("data/moves_if.json")
REQUEST_DELAY = 0.1   # secondes

# Corrections manuelles : nom IF wiki → slug PokeAPI exact
# Nécessaire quand le nom IF diverge du nom PokeAPI
MANUAL_SLUGS: dict[str, str] = {
    "Frustration":         "return",          # IF renomme Return → Frustration ?
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


def fetch_fr_name(slug: str) -> str | None:
    try:
        resp = requests.get(POKEAPI_MOVE.format(slug), timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        for entry in data.get("names", []):
            if entry["language"]["name"] == "fr":
                return entry["name"]
        return None
    except Exception as e:
        LOGGER.debug("PokeAPI error '%s': %s", slug, e)
        return None


def main() -> None:
    if not MOVES_FILE.exists():
        raise FileNotFoundError("data/moves_if.json not found — run extract_moves_if.py first")

    moves = json.loads(MOVES_FILE.read_text())
    to_enrich = [m for m in moves if not m.get("name_fr")]
    LOGGER.info("%d moves à enrichir en FR (sur %d)", len(to_enrich), len(moves))

    found = not_found = 0

    for i, move in enumerate(moves):
        if move.get("name_fr"):
            continue

        slug    = to_slug(move["name_en"])
        name_fr = fetch_fr_name(slug)

        if name_fr:
            move["name_fr"] = name_fr
            found += 1
        else:
            LOGGER.debug("FR not found: '%s' (slug: %s)", move["name_en"], slug)
            not_found += 1

        if (i + 1) % 100 == 0:
            # Sauvegarde intermédiaire
            MOVES_FILE.write_text(json.dumps(moves, ensure_ascii=False, indent=2))
            LOGGER.info("[%d/%d] %d trouvés, %d non trouvés", i + 1, len(moves), found, not_found)

        time.sleep(REQUEST_DELAY)

    MOVES_FILE.write_text(json.dumps(moves, ensure_ascii=False, indent=2))
    LOGGER.info("Terminé — %d FR trouvés | %d non trouvés", found, not_found)

    # Résumé des non trouvés
    missing = [m["name_en"] for m in moves if not m.get("name_fr")]
    if missing:
        LOGGER.warning("%d moves sans nom FR : %s", len(missing), missing[:20])


if __name__ == "__main__":
    main()
