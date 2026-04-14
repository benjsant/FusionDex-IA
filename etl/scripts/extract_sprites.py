"""
ETL Step 9 — Download & extract fusion sprites from infinitefusion.net.

Optimisations :
  - Filtre par IDs IF réels (data/pokedex_if.json) → ignore les sprites hors-jeu
  - Par défaut : sprites principaux uniquement (alt="")
  - Option --alts : inclut les variantes communautaires (a, b, c...)
  - Idempotent : skip les sprites déjà extraits (sauf --force)
  - Une seule requête par spritesheet → crop de tous les body_ids en une passe

Sprite grid layout (CustomSpriteExtracter.rb) :
  Taille : 96×96 px | Colonnes : 20
  Position : col = body_id % 20 / row = body_id // 20

URLs (pif-downloadables/Settings.rb) :
  Spritesheets : https://infinitefusion.net/customsprites/spritesheets/spritesheets_custom/{head}/{head}{alt}.png
  Credits      : https://infinitefusion.net/customsprites/Sprite_Credits.csv
  Sprite list  : https://raw.githubusercontent.com/infinitefusion/pif-downloadables/master/CUSTOM_SPRITES
"""

from __future__ import annotations

import io
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import requests
from PIL import Image

from etl.utils.io import load_json
from etl.utils.logging import setup_logging

LOGGER = setup_logging(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR       = Path(__file__).resolve().parents[2] / "data"
SPRITES_DIR    = DATA_DIR / "sprites"
CREDITS_OUT    = DATA_DIR / "sprite_credits.csv"
POKEDEX_IF     = DATA_DIR / "pokedex_if.json"

# ── URLs ──────────────────────────────────────────────────────────────────────
CUSTOM_SPRITES_URL   = "https://raw.githubusercontent.com/infinitefusion/pif-downloadables/master/CUSTOM_SPRITES"
SPRITE_CREDITS_URL   = "https://infinitefusion.net/customsprites/Sprite_Credits.csv"
SPRITESHEET_BASE_URL = "https://infinitefusion.net/customsprites/spritesheets/spritesheets_custom"

# ── Constants ─────────────────────────────────────────────────────────────────
SPRITE_SIZE    = 96
GRID_COLS      = 20
DOWNLOAD_DELAY = 2.0    # secondes entre deux spritesheets (respectful)

SPRITE_RE = re.compile(r"^(\d+)\.(\d+)([a-z]*)\.png$")


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_if_ids() -> set[int]:
    """
    Charge les IF IDs depuis data/pokedex_if.json.
    Si le fichier n'existe pas encore (ETL lancé hors pipeline), retourne un set vide
    qui désactive le filtre.
    """
    if not POKEDEX_IF.exists():
        LOGGER.warning(
            "pokedex_if.json not found — no ID filter applied (run extract_pokedex_if.py first)"
        )
        return set()
    entries = load_json(POKEDEX_IF)
    ids = {e["if_id"] for e in entries}
    LOGGER.info("Loaded %d IF Pokémon IDs from pokedex_if.json", len(ids))
    return ids


def fetch_text(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_bytes(url: str) -> bytes | None:
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.content
        LOGGER.warning("HTTP %s — %s", resp.status_code, url)
        return None
    except requests.RequestException as e:
        LOGGER.warning("Request failed %s — %s", url, e)
        return None


def crop_sprite(sheet: Image.Image, body_id: int) -> Image.Image:
    col = body_id % GRID_COLS
    row = body_id // GRID_COLS
    x   = col * SPRITE_SIZE
    y   = row * SPRITE_SIZE
    return sheet.crop((x, y, x + SPRITE_SIZE, y + SPRITE_SIZE))


def parse_and_filter(
    raw: str,
    if_ids: set[int],
    include_alts: bool,
) -> dict[tuple[int, str], list[int]]:
    """
    Parse CUSTOM_SPRITES et retourne {(head_id, alt): [body_id, ...]}
    en appliquant deux filtres :
      1. head_id ET body_id doivent être dans if_ids (si if_ids non vide)
      2. Les alts (a, b, c...) sont exclus sauf si include_alts=True
    """
    groups: dict[tuple[int, str], list[int]] = defaultdict(list)
    total = skipped_id = skipped_alt = 0

    for line in raw.splitlines():
        line = line.strip()
        m    = SPRITE_RE.match(line)
        if not m:
            continue

        total   += 1
        head_id  = int(m.group(1))
        body_id  = int(m.group(2))
        alt      = m.group(3)

        # Filtre 1 — IDs IF uniquement
        if if_ids and (head_id not in if_ids or body_id not in if_ids):
            skipped_id += 1
            continue

        # Filtre 2 — alts optionnels
        if alt and not include_alts:
            skipped_alt += 1
            continue

        groups[(head_id, alt)].append(body_id)

    kept = sum(len(v) for v in groups.values())
    LOGGER.info(
        "CUSTOM_SPRITES: %d total → gardés=%d / filtrés hors-IF=%d / alts exclus=%d",
        total, kept, skipped_id, skipped_alt,
    )
    return groups


# ── Core ──────────────────────────────────────────────────────────────────────

def download_credits() -> None:
    LOGGER.info("Downloading Sprite_Credits.csv...")
    raw = fetch_text(SPRITE_CREDITS_URL)
    CREDITS_OUT.write_text(raw, encoding="utf-8")
    LOGGER.info("Credits → %s", CREDITS_OUT)


def extract_sprites(force: bool, include_alts: bool) -> None:
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)

    if_ids   = load_if_ids()
    raw_list = fetch_text(CUSTOM_SPRITES_URL)
    groups   = parse_and_filter(raw_list, if_ids, include_alts)

    n_sheets  = len(groups)
    n_sprites = sum(len(v) for v in groups.values())
    LOGGER.info("À télécharger : %d spritesheets / %d sprites", n_sheets, n_sprites)

    extracted = skipped = failed = 0

    for idx, ((head_id, alt), body_ids) in enumerate(sorted(groups.items()), 1):

        # Skip si tous les sprites existent déjà
        if not force:
            missing = [
                b for b in body_ids
                if not (SPRITES_DIR / f"{head_id}.{b}{alt}.png").exists()
            ]
            if not missing:
                skipped += len(body_ids)
                continue
            body_ids = missing

        # Télécharge la spritesheet une seule fois
        sheet_url  = f"{SPRITESHEET_BASE_URL}/{head_id}/{head_id}{alt}.png"
        sheet_data = fetch_bytes(sheet_url)

        if sheet_data is None:
            LOGGER.warning("[%d/%d] Spritesheet manquante head=%d alt='%s'", idx, n_sheets, head_id, alt)
            failed += len(body_ids)
            continue

        try:
            sheet = Image.open(io.BytesIO(sheet_data)).convert("RGBA")
        except Exception as e:
            LOGGER.warning("Impossible d'ouvrir la spritesheet %s : %s", sheet_url, e)
            failed += len(body_ids)
            continue

        # Crop de tous les body_ids en une seule passe
        for body_id in body_ids:
            out_path = SPRITES_DIR / f"{head_id}.{body_id}{alt}.png"
            try:
                crop_sprite(sheet, body_id).save(out_path, format="PNG")
                extracted += 1
            except Exception as e:
                LOGGER.warning("Crop échoué head=%d body=%d : %s", head_id, body_id, e)
                failed += 1

        LOGGER.info("[%d/%d] head=%d alt='%s' → %d sprites", idx, n_sheets, head_id, alt, len(body_ids))
        time.sleep(DOWNLOAD_DELAY)

    LOGGER.info(
        "Terminé — extraits=%d / ignorés=%d / échecs=%d",
        extracted, skipped, failed,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    force        = "--force" in sys.argv
    include_alts = "--alts"  in sys.argv
    download_credits()
    extract_sprites(force=force, include_alts=include_alts)


if __name__ == "__main__":
    main()
