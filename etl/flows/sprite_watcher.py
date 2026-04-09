"""
Prefect flow — Sprite update watcher.

Surveille le repo infinitefusion/pif-downloadables (branche master).
Quand un nouveau commit est détecté sur CUSTOM_SPRITES ou Settings.rb :
  1. Compare les listes de sprites (ancien SHA vs nouveau SHA)
  2. Identifie les sprites ajoutés / supprimés
  3. Télécharge et extrait les nouveaux sprites automatiquement
  4. Met à jour SHA_FILE pour la prochaine exécution

Lancement manuel :
  python -m etl.flows.sprite_watcher

Lancement Prefect planifié (toutes les 24h) :
  prefect deployment run sprite-watcher/daily
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import requests
from prefect import flow, task
from prefect.logging import get_run_logger

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SHA_FILE = DATA_DIR / "sprites_last_sha.txt"

# ── GitHub API ────────────────────────────────────────────────────────────────
REPO          = "infinitefusion/pif-downloadables"
BRANCH        = "master"
WATCHED_FILES = {"CUSTOM_SPRITES", "Settings.rb"}
RAW_BASE      = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
API_BASE      = f"https://api.github.com/repos/{REPO}"


# ── Tasks ─────────────────────────────────────────────────────────────────────

@task(name="fetch-latest-sha")
def fetch_latest_sha() -> str:
    """Récupère le SHA du dernier commit sur master."""
    logger = get_run_logger()
    resp = requests.get(f"{API_BASE}/commits/{BRANCH}", timeout=15)
    resp.raise_for_status()
    sha = resp.json()["sha"]
    logger.info("Latest SHA: %s", sha[:8])
    return sha


@task(name="read-local-sha")
def read_local_sha() -> str | None:
    """Lit le SHA connu localement."""
    if SHA_FILE.exists():
        return SHA_FILE.read_text().strip() or None
    return None


@task(name="fetch-sprite-list")
def fetch_sprite_list(sha: str) -> set[str]:
    """Récupère la liste CUSTOM_SPRITES pour un SHA donné."""
    url  = f"https://raw.githubusercontent.com/{REPO}/{sha}/CUSTOM_SPRITES"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return {
        line.strip()
        for line in resp.text.splitlines()
        if line.strip().endswith(".png")
    }


@task(name="compute-diff")
def compute_diff(
    old_sprites: set[str],
    new_sprites: set[str],
) -> dict[str, list[str]]:
    """Calcule les sprites ajoutés et supprimés."""
    logger   = get_run_logger()
    added    = sorted(new_sprites - old_sprites)
    removed  = sorted(old_sprites - new_sprites)
    logger.info("Diff — added: %d / removed: %d", len(added), len(removed))
    return {"added": added, "removed": removed}


@task(name="extract-new-sprites")
def extract_new_sprites() -> None:
    """Lance extract_sprites.py pour télécharger les nouveaux sprites."""
    logger = get_run_logger()
    logger.info("Launching sprite extraction...")
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "extract_sprites.py")],
        check=False,
    )
    if result.returncode != 0:
        logger.error("extract_sprites.py failed (code %d)", result.returncode)
    else:
        logger.info("Extraction complete.")


@task(name="save-sha")
def save_sha(sha: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SHA_FILE.write_text(sha)
    get_run_logger().info("SHA saved: %s", sha[:8])


# ── Flow ──────────────────────────────────────────────────────────────────────

@flow(name="sprite-watcher", log_prints=True)
def sprite_watcher_flow() -> None:
    """
    Détecte les nouveaux spritepacks IF et extrait les nouveaux sprites.
    À planifier toutes les 24h via Prefect.
    """
    logger = get_run_logger()

    latest_sha = fetch_latest_sha()
    local_sha  = read_local_sha()

    if local_sha == latest_sha:
        logger.info("No update detected (SHA=%s). Nothing to do.", latest_sha[:8])
        return

    logger.info(
        "New commit detected: %s → %s",
        (local_sha or "none")[:8],
        latest_sha[:8],
    )

    # Diff sprite lists
    if local_sha:
        old_sprites = fetch_sprite_list(local_sha)
        new_sprites = fetch_sprite_list(latest_sha)
        diff        = compute_diff(old_sprites, new_sprites)

        if diff["added"]:
            logger.info("New sprites:\n  %s", "\n  ".join(diff["added"][:20]))
            if len(diff["added"]) > 20:
                logger.info("  ... and %d more", len(diff["added"]) - 20)

        if diff["removed"]:
            logger.info("Removed sprites: %d", len(diff["removed"]))

        if not diff["added"] and not diff["removed"]:
            logger.info("Sprite list unchanged — only Settings or other files updated.")
            save_sha(latest_sha)
            return
    else:
        logger.info("First run — full extraction.")

    # Téléchargement des nouveaux sprites
    extract_new_sprites()
    save_sha(latest_sha)
    logger.info("Sprite watcher flow complete.")


if __name__ == "__main__":
    sprite_watcher_flow()
