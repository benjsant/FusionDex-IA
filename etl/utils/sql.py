"""Generic SQL helpers for ETL load scripts."""

from __future__ import annotations


def load_id_map(
    conn,
    table: str,
    key_col: str = "name_en",
    *,
    where: str = "",
    lower: bool = True,
) -> dict:
    """Return {key_col: id} for rows of `table`.

    Args:
        conn:    psycopg2 connection.
        table:   table name.
        key_col: column used as dict key.
        where:   optional WHERE clause (without the `WHERE` keyword).
        lower:   if True, `.lower()` keys. Skipped for non-string columns.
    """
    sql = f"SELECT id, {key_col} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    if lower:
        return {k.lower(): db_id for db_id, k in rows if k is not None}
    return {k: db_id for db_id, k in rows if k is not None}
