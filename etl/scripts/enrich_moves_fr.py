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
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

POKEAPI_MOVE  = "https://pokeapi.co/api/v2/move/{}"
MOVES_FILE    = Path("data/moves_if.json")
MAX_WORKERS   = 4
REQUEST_DELAY = 0.05   # secondes par worker

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


def _enrich_one(move: dict) -> tuple[dict, str | None]:
    """Fetch FR name for one move. Returns (move, name_fr_or_None)."""
    slug    = to_slug(move["name_en"])
    name_fr = fetch_fr_name(slug)
    time.sleep(REQUEST_DELAY)
    return move, name_fr


def main() -> None:
    if not MOVES_FILE.exists():
        raise FileNotFoundError("data/moves_if.json not found — run extract_moves_if.py first")

    moves = json.loads(MOVES_FILE.read_text())
    to_enrich = [m for m in moves if not m.get("name_fr")]
    LOGGER.info("%d moves à enrichir en FR (sur %d)", len(to_enrich), len(moves))

    found = not_found = 0
    lock  = threading.Lock()
    done  = 0

    def save() -> None:
        MOVES_FILE.write_text(json.dumps(moves, ensure_ascii=False, indent=2))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_enrich_one, m): m for m in to_enrich}
        for future in as_completed(futures):
            move, name_fr = future.result()
            with lock:
                done += 1
                if name_fr:
                    move["name_fr"] = name_fr
                    found += 1
                else:
                    LOGGER.debug("FR not found: '%s'", move["name_en"])
                    not_found += 1
                if done % 100 == 0:
                    save()
                    LOGGER.info("[%d/%d] %d trouvés, %d non trouvés", done, len(to_enrich), found, not_found)

    save()
    LOGGER.info("Terminé — %d FR trouvés | %d non trouvés", found, not_found)

    missing = [m["name_en"] for m in moves if not m.get("name_fr")]
    if missing:
        LOGGER.warning("%d moves sans nom FR : %s", len(missing), missing[:20])


if __name__ == "__main__":
    main()
