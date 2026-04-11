"""
ETL — Load sprite credits from the Infinite Fusion community CSV.

Source : data/sprite_credits.csv (one row per sprite variant)
Format :
    1,xillo,main,
    1.1,zoroark73,main,
    1.100a,aquaticpanic,main,
    1.4.7,someone,main,              → triple fusion (skipped)
    1.104,barnabyjjones & emisys,main,  → multi-creator, split on '&'
    89.549,vikku__,alt,"regional,alolan"

Rules :
  - Base sprites (N)        → fusion_sprite(head=N, body=N)
  - Fusion sprites (N.M)    → fusion_sprite(head=N, body=M)
  - Triple fusions (N.M.K)  → skipped (schema mismatch)
  - Variants (1.100a, 1.100b) → skipped (not shipped on disk)
  - Only rows whose (head, body) both exist in pokemon table are kept
  - Multi-creator rows split on '&' → M:N via fusion_sprite_creator

Idempotence :
  community sprites are wiped then reinserted
  (source='community' + is_custom=True marks them as CSV-sourced)

Target tables :
  creator
  fusion_sprite (source='community')
  fusion_sprite_creator
"""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path

import psycopg2.extras

from etl.utils.db import get_pg_connection as get_connection

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CSV_FILE = Path("data/sprite_credits.csv")

# N  or  N.M  or  N.M.K   with optional lowercase letter suffix
ID_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?([a-z]+)?$")


def parse_id(id_str: str) -> tuple[int, int] | None:
    """Return (head, body) or None if the row must be skipped."""
    m = ID_RE.match(id_str)
    if not m:
        return None
    head_s, body_s, third_s, variant = m.groups()
    if third_s:            # triple fusion — schema mismatch
        return None
    if variant:            # a/b/c — not shipped as files
        return None
    head = int(head_s)
    body = int(body_s) if body_s else head  # base sprite = head.head
    return head, body


def load_sprite_credits(conn) -> None:
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"{CSV_FILE} not found")

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM pokemon")
        valid_ids: set[int] = {row[0] for row in cur.fetchall()}
    LOGGER.info("Valid pokemon ids: %d", len(valid_ids))

    pair_creators: dict[tuple[int, int], list[str]] = {}
    all_creators: set[str] = set()
    skipped_triple = 0
    skipped_variant = 0
    skipped_unknown_pokemon = 0
    skipped_malformed = 0

    with CSV_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                skipped_malformed += 1
                continue
            id_str = row[0].strip()
            creators_str = row[1].strip()

            m = ID_RE.match(id_str)
            if not m:
                skipped_malformed += 1
                continue
            _, _, third_s, variant = m.groups()
            if third_s:
                skipped_triple += 1
                continue
            if variant:
                skipped_variant += 1
                continue

            parsed = parse_id(id_str)
            if not parsed:
                skipped_malformed += 1
                continue
            head, body = parsed

            if head not in valid_ids or body not in valid_ids:
                skipped_unknown_pokemon += 1
                continue

            creators = [c.strip() for c in creators_str.split("&") if c.strip()]
            if not creators:
                continue

            # Keep first occurrence per (head, body) — dedupe variants
            if (head, body) not in pair_creators:
                pair_creators[(head, body)] = creators
                all_creators.update(creators)

    LOGGER.info(
        "Parsed: %d unique sprites | %d creators | skipped %d triples, %d variants, %d unknown-pokemon, %d malformed",
        len(pair_creators), len(all_creators),
        skipped_triple, skipped_variant, skipped_unknown_pokemon, skipped_malformed,
    )

    with conn.cursor() as cur:
        # ── Idempotence : wipe community sprites ─────────────────────────────
        cur.execute(
            """DELETE FROM fusion_sprite_creator
               WHERE fusion_sprite_id IN (
                   SELECT id FROM fusion_sprite WHERE source = 'community'
               )"""
        )
        cur.execute("DELETE FROM fusion_sprite WHERE source = 'community'")
        LOGGER.info("Wiped previous community sprites")

        # ── Insert creators ──────────────────────────────────────────────────
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO creator (name) VALUES %s ON CONFLICT (name) DO NOTHING",
            [(n,) for n in sorted(all_creators)],
            page_size=1000,
        )
        cur.execute("SELECT id, name FROM creator")
        creator_id_by_name: dict[str, int] = {name: cid for cid, name in cur.fetchall()}
        LOGGER.info("Creators in DB: %d", len(creator_id_by_name))

        # ── Insert fusion_sprite ─────────────────────────────────────────────
        sprite_rows = [
            (h, b, f"{h}.{b}.png", True, True, "community")
            for (h, b) in pair_creators
        ]
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO fusion_sprite
               (head_id, body_id, sprite_path, is_custom, is_default, source)
               VALUES %s""",
            sprite_rows,
            page_size=2000,
        )
        LOGGER.info("Inserted %d fusion_sprite rows", len(sprite_rows))

        # ── Build (head, body) → sprite_id map ───────────────────────────────
        cur.execute(
            "SELECT id, head_id, body_id FROM fusion_sprite WHERE source = 'community'"
        )
        sprite_id_by_pair: dict[tuple[int, int], int] = {
            (h, b): sid for sid, h, b in cur.fetchall()
        }

        # ── Insert fusion_sprite_creator ─────────────────────────────────────
        join_rows: list[tuple[int, int]] = []
        for (h, b), creators in pair_creators.items():
            sid = sprite_id_by_pair.get((h, b))
            if sid is None:
                continue
            for cname in creators:
                cid = creator_id_by_name.get(cname)
                if cid is not None:
                    join_rows.append((sid, cid))

        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO fusion_sprite_creator (fusion_sprite_id, creator_id)
               VALUES %s ON CONFLICT DO NOTHING""",
            join_rows,
            page_size=2000,
        )
        LOGGER.info("Inserted %d fusion_sprite_creator rows", len(join_rows))

        conn.commit()


def main() -> None:
    LOGGER.info("Connecting to PostgreSQL...")
    conn = get_connection()
    try:
        load_sprite_credits(conn)
    except Exception:
        conn.rollback()
        LOGGER.exception("load_sprite_credits failed — rolling back")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
