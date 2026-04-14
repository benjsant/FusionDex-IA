"""
ETL — Inherit moves from pre-evolutions into pokemon_move.

Pattern ported from prediction_dex/etl_previous_evolution.py, but uses a
recursive SQL CTE instead of PokeAPI walks: the evolution chain is already
materialised in pokemon_evolution, so we can join directly.

Rules:
  - Charizard inherits from Charmeleon AND Charmander (transitive ancestors)
  - Only moves the descendant doesn't already know (any method) are inserted
  - Inherited rows: method='before_evolution', level=NULL, source='base'
  - Idempotent: ON CONFLICT DO NOTHING on (pokemon_id, move_id, method)
"""

from __future__ import annotations

from etl.utils.db import pg_connection
from etl.utils.logging import setup_logging

LOGGER = setup_logging(__name__)


SQL = """
WITH RECURSIVE ancestors AS (
    SELECT evolves_into_id AS pokemon_id,
           pokemon_id       AS ancestor_id
    FROM pokemon_evolution
    UNION
    SELECT a.pokemon_id,
           pe.pokemon_id
    FROM ancestors a
    JOIN pokemon_evolution pe ON pe.evolves_into_id = a.ancestor_id
)
INSERT INTO pokemon_move (pokemon_id, move_id, method, level, source)
SELECT DISTINCT
    a.pokemon_id,
    pm.move_id,
    'before_evolution'::varchar(20),
    NULL::integer,
    'base'::varchar(20)
FROM ancestors a
JOIN pokemon_move pm ON pm.pokemon_id = a.ancestor_id
WHERE pm.method <> 'before_evolution'
  AND NOT EXISTS (
      SELECT 1 FROM pokemon_move existing
      WHERE existing.pokemon_id = a.pokemon_id
        AND existing.move_id    = pm.move_id
  )
ON CONFLICT (pokemon_id, move_id, method) DO NOTHING;
"""


def main() -> None:
    with pg_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pokemon_move WHERE method = 'before_evolution'")
        before = cur.fetchone()[0]

        cur.execute(SQL)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM pokemon_move WHERE method = 'before_evolution'")
        after = cur.fetchone()[0]

    LOGGER.info(
        "before_evolution rows: %d → %d (+%d inherited)",
        before, after, after - before,
    )


if __name__ == "__main__":
    main()
