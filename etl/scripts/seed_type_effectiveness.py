"""
ETL Step 9 — Seed types (EN+FR) and type_effectiveness from table_type.csv.

Source: etl/scripts/data/table_type.csv (issu du predictiondex)
Colonnes CSV : type_attaquant, type_defenseur, multiplicateur (noms français)

Ordre d'exécution : APRÈS load_db.py (types EN déjà en table, on ajoute name_fr)

Idempotent : ON CONFLICT DO NOTHING / DO UPDATE SET name_fr.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from etl.utils.db import pg_connection
from etl.utils.logging import setup_logging

LOGGER = setup_logging(__name__)

CSV_PATH = Path(__file__).parent / "data" / "table_type.csv"

# Correspondance FR ↔ EN pour les 18 types standards
FR_TO_EN: dict[str, str] = {
    "Normal":   "Normal",
    "Feu":      "Fire",
    "Eau":      "Water",
    "Électrik": "Electric",
    "Plante":   "Grass",
    "Glace":    "Ice",
    "Combat":   "Fighting",
    "Poison":   "Poison",
    "Sol":      "Ground",
    "Vol":      "Flying",
    "Psy":      "Psychic",
    "Insecte":  "Bug",
    "Roche":    "Rock",
    "Spectre":  "Ghost",
    "Dragon":   "Dragon",
    "Ténèbres": "Dark",
    "Acier":    "Steel",
    "Fée":      "Fairy",
}


def seed_types(cur) -> dict[str, int]:
    """
    Insère les 18 types avec name_en + name_fr.
    Si le type existe déjà (inséré par load_db avec name_en uniquement),
    on met à jour name_fr via DO UPDATE.
    Retourne {name_en: id}.
    """
    for name_fr, name_en in FR_TO_EN.items():
        cur.execute(
            """
            INSERT INTO type (name_en, name_fr, is_triple_fusion_type)
            VALUES (%s, %s, FALSE)
            ON CONFLICT (name_en) DO UPDATE
                SET name_fr = EXCLUDED.name_fr
            """,
            (name_en, name_fr),
        )

    cur.execute("SELECT id, name_en FROM type WHERE is_triple_fusion_type = FALSE")
    type_map: dict[str, int] = {name_en: tid for tid, name_en in cur.fetchall()}
    LOGGER.info("Types seedés/mis à jour : %d", len(type_map))
    return type_map


def seed_effectiveness(cur, type_map: dict[str, int]) -> None:
    """
    Lit table_type.csv (noms FR) et insère les lignes non-neutres
    dans type_effectiveness.
    """
    if not CSV_PATH.exists():
        LOGGER.error("CSV introuvable : %s", CSV_PATH)
        return

    inserted = skipped = neutral = 0

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mult = Decimal(row["multiplicateur"])

            if mult == Decimal("1"):
                neutral += 1
                continue

            atk_en = FR_TO_EN.get(row["type_attaquant"])
            def_en = FR_TO_EN.get(row["type_defenseur"])

            if atk_en is None or def_en is None:
                LOGGER.warning(
                    "Type FR inconnu : %s / %s",
                    row["type_attaquant"], row["type_defenseur"]
                )
                skipped += 1
                continue

            atk_id = type_map.get(atk_en)
            def_id = type_map.get(def_en)
            if atk_id is None or def_id is None:
                skipped += 1
                continue

            cur.execute(
                """
                INSERT INTO type_effectiveness (attacking_type_id, defending_type_id, multiplier)
                VALUES (%s, %s, %s)
                ON CONFLICT (attacking_type_id, defending_type_id) DO NOTHING
                """,
                (atk_id, def_id, mult),
            )
            if cur.rowcount:
                inserted += 1

    LOGGER.info(
        "type_effectiveness : %d insérés | %d neutres ignorés | %d inconnus",
        inserted, neutral, skipped,
    )


def main() -> None:
    with pg_connection() as conn:
        cur = conn.cursor()
        type_map = seed_types(cur)
        seed_effectiveness(cur, type_map)
        conn.commit()
        cur.close()
    LOGGER.info("Terminé.")


if __name__ == "__main__":
    main()
