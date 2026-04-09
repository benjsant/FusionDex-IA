"""
ETL Step 8 — Load all transformed data into PostgreSQL.

Loading order respects FK constraints:
  1. generation
  2. type
  3. ability
  4. move
  5. tm
  6. pokemon
  7. pokemon_type
  8. pokemon_ability
  9. pokemon_evolution
  10. location
  11. pokemon_location
  12. pokemon_move

All inserts use ON CONFLICT DO NOTHING → idempotent / re-runnable.

Sources:
  data/pokedex_if.json
  data/pokemon_stats.json
  data/moves_if.json
  data/tms_if.json
  data/abilities_if.json
  data/locations_if.json
  data/movesets_merged.json
  data/evolutions_base.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

from etl.utils.db import get_pg_connection

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# IF overrides for evolution methods (from Differences_with_the_official_games wiki page)
# Format: (from_name_en, into_name_en): [(trigger, min_level, item_en, if_notes)]
# Multiple tuples = alternative conditions
IF_EVOLUTION_OVERRIDES: dict[tuple[str, str], list[tuple]] = {
    ("golbat",      "crobat"):      [("level_up",  40,   None,         "Level 40 (no friendship)")],
    ("poliwhirl",   "politoed"):    [("level_up",  37,   None,         "Level 37 OR King's Rock"),
                                     ("use_item",  None, "kings-rock", "King's Rock")],
    ("kadabra",     "alakazam"):    [("level_up",  40,   None,         "Level 40 OR Linking Cord"),
                                     ("use_item",  None, "linking-cord", "Linking Cord")],
    ("machoke",     "machamp"):     [("level_up",  40,   None,         "Level 40 OR Linking Cord"),
                                     ("use_item",  None, "linking-cord", "Linking Cord")],
    ("graveler",    "golem"):       [("level_up",  40,   None,         "Level 40 OR Linking Cord"),
                                     ("use_item",  None, "linking-cord", "Linking Cord")],
    ("slowpoke",    "slowking"):    [("use_item",  None, "water-stone",  "Water Stone OR King's Rock"),
                                     ("use_item",  None, "kings-rock",  "King's Rock")],
    ("magneton",    "magnezone"):   [("use_item",  None, "magnet-stone", "Magnet Stone (IF-specific)")],
    ("haunter",     "gengar"):      [("level_up",  40,   None,         "Level 40 OR Linking Cord"),
                                     ("use_item",  None, "linking-cord", "Linking Cord")],
    ("onix",        "steelix"):     [("level_up",  40,   None,         "Level 40 OR Metal Coat"),
                                     ("use_item",  None, "metal-coat",  "Metal Coat")],
    ("rhydon",      "rhyperior"):   [("level_up",  55,   None,         "Level 55 OR Protector"),
                                     ("use_item",  None, "protector",   "Protector")],
    ("chansey",     "blissey"):     [("level_up",  42,   None,         "Level 42 (no friendship)")],
    ("scyther",     "scizor"):      [("level_up",  40,   None,         "Level 40 OR Metal Coat"),
                                     ("use_item",  None, "metal-coat",  "Metal Coat")],
    ("seadra",      "kingdra"):     [("level_up",  50,   None,         "Level 50 OR Dragon Scale"),
                                     ("use_item",  None, "dragon-scale", "Dragon Scale")],
    ("electabuzz",  "electivire"):  [("level_up",  50,   None,         "Level 50 OR Electirizer"),
                                     ("use_item",  None, "electirizer", "Electirizer")],
    ("magmar",      "magmortar"):   [("level_up",  50,   None,         "Level 50 OR Magmarizer"),
                                     ("use_item",  None, "magmarizer",  "Magmarizer")],
    ("eevee",       "espeon"):      [("use_item",  None, "sun-stone",   "Sun Stone (no daytime/friendship)")],
    ("eevee",       "umbreon"):     [("use_item",  None, "moon-stone",  "Moon Stone")],
    ("eevee",       "leafeon"):     [("use_item",  None, "leaf-stone",  "Leaf Stone")],
    ("eevee",       "glaceon"):     [("use_item",  None, "ice-stone",   "Ice Stone")],
    ("eevee",       "sylveon"):     [("use_item",  None, "shiny-stone", "Shiny Stone")],
    ("porygon",     "porygon2"):    [("use_item",  None, "up-grade",    "Upgrade item")],
    ("pichu",       "pikachu"):     [("level_up",  15,   None,         "Level 15 (no friendship)")],
    ("cleffa",      "clefairy"):    [("level_up",  15,   None,         "Level 15 (no friendship)")],
    ("igglybuff",   "jigglypuff"):  [("level_up",  15,   None,         "Level 15")],
    ("togepi",      "togetic"):     [("level_up",  15,   None,         "Level 15")],
    ("gligar",      "gliscor"):     [("use_item",  None, "dusk-stone",  "Dusk Stone (no Razor Fang/night)")],
    ("sneasel",     "weavile"):     [("use_item",  None, "ice-stone",   "Ice Stone")],
    ("porygon2",    "porygon-z"):   [("use_item",  None, "dubious-disc","Dubious Disc")],
    ("smoochum",    "jynx"):        [("level_up",  21,   None,         "Level 21 (was 30)")],
    ("elekid",      "electabuzz"):  [("level_up",  21,   None,         "Level 21 (was 30)")],
    ("magby",       "magmar"):      [("level_up",  21,   None,         "Level 21 (was 30)")],
    ("azurill",     "marill"):      [("level_up",  15,   None,         "Level 15 (no friendship)")],
    ("munchlax",    "snorlax"):     [("level_up",  30,   None,         "Level 30 (no friendship)")],
    ("mantyke",     "mantine"):     [("level_up",  20,   None,         "Level 20 (no Remoraid in party)")],
    ("kirlia",      "gallade"):     [("use_item",  None, "dawn-stone",  "Dawn Stone (any gender)")],
    ("dusclops",    "dusknoir"):    [("level_up",  50,   None,         "Level 50 OR Reaper Cloth"),
                                     ("use_item",  None, "reaper-cloth","Reaper Cloth")],
    ("nosepass",    "probopass"):   [("use_item",  None, "magnet-stone","Magnet Stone (IF-specific)")],
    ("riolu",       "lucario"):     [("level_up",  20,   None,         "Level 20 (no friendship/daytime)")],
    ("feebas",      "milotic"):     [("level_up",  35,   None,         "Level 35 OR Prism Scale"),
                                     ("use_item",  None, "prism-scale", "Prism Scale")],
    ("budew",       "roselia"):     [("level_up",  15,   None,         "Level 15")],
    ("buneary",     "lopunny"):     [("level_up",  22,   None,         "Level 22 (no friendship)")],
    ("snorunt",     "froslass"):    [("use_item",  None, "dawn-stone",  "Dawn Stone (any gender)")],
    ("phantump",    "trevenant"):   [("level_up",  40,   None,         "Level 40 OR Linking Cord"),
                                     ("use_item",  None, "linking-cord","Linking Cord")],
    ("sliggoo",     "goodra"):      [("level_up",  50,   None,         "Level 50 (no rain required)")],
    ("pumpkaboo",   "gourgeist"):   [("level_up",  40,   None,         "Level 40 (no trade)")],
    ("swirlix",     "slurpuff"):    [("level_up",  35,   None,         "Level 35 (no trade+item)")],
}


# ─── Loader helpers ───────────────────────────────────────────────────────────

def upsert(conn, table: str, rows: list[dict], conflict_col: str = "id") -> int:
    """Generic single-column-conflict upsert using execute_values."""
    if not rows:
        return 0
    cols   = list(rows[0].keys())
    values = [[r[c] for c in cols] for r in rows]
    sql    = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s "
        f"ON CONFLICT ({conflict_col}) DO NOTHING"
    )
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    conn.commit()
    return len(rows)


# ─── Load functions per table ─────────────────────────────────────────────────

def load_generations(conn) -> dict[int, int]:
    """Seed generation table. Returns {gen_number: db_id}."""
    GENS = [
        (1, "generation-i",   "génération-i"),
        (2, "generation-ii",  "génération-ii"),
        (3, "generation-iii", "génération-iii"),
        (4, "generation-iv",  "génération-iv"),
        (5, "generation-v",   "génération-v"),
        (6, "generation-vi",  "génération-vi"),
        (7, "generation-vii", "génération-vii"),
    ]
    with conn.cursor() as cur:
        for num, name_en, name_fr in GENS:
            cur.execute(
                "INSERT INTO generation (name_en, name_fr) VALUES (%s, %s) "
                "ON CONFLICT (name_en) DO NOTHING",
                (name_en, name_fr),
            )
        conn.commit()
        cur.execute("SELECT id, name_en FROM generation")
        rows = cur.fetchall()

    gen_map = {}
    for db_id, name_en in rows:
        num = int(name_en.split("-")[-1].replace("i", "1").replace("v", "5").replace("x", "10"))
        # Use Roman numeral position for mapping
        roman = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7}
        suffix = name_en.split("-")[-1]
        gen_map[roman.get(suffix, 0)] = db_id

    LOGGER.info("Loaded %d generations", len(gen_map))
    return gen_map


def load_types(conn, moves: list[dict]) -> dict[str, int]:
    """Seed type table from move data. Returns {name_en_lower: db_id}."""
    # Capitalize to match the canonical form inserted by seed_type_effectiveness
    type_names_en = {m["type_en"].capitalize() for m in moves if m.get("type_en")}

    # The 9 triple-fusion types — added manually since not in List of Moves
    TRIPLE_FUSION_TYPES = {
        "Ice/fire/electric", "Fire/water/electric", "Water/ground/flying",
        "Dragon/ghost/steel", "Ice/fire/electric/dragon", "Psychic/grass/steel",
        "Psychic/steel/bug", "Ice/rock/steel", "Fire/water/grass",
    }

    with conn.cursor() as cur:
        for name in sorted(type_names_en):
            is_tf = name in TRIPLE_FUSION_TYPES
            cur.execute(
                "INSERT INTO type (name_en, is_triple_fusion_type) VALUES (%s, %s) "
                "ON CONFLICT (name_en) DO NOTHING",
                (name, is_tf),
            )
        conn.commit()
        cur.execute("SELECT id, name_en FROM type")
        rows = cur.fetchall()

    type_map = {name.lower(): db_id for db_id, name in rows}
    LOGGER.info("Loaded %d types", len(type_map))
    return type_map


def load_abilities(conn, abilities: list[dict]) -> dict[str, int]:
    """Returns {name_en_lower: db_id}."""
    with conn.cursor() as cur:
        for ab in abilities:
            cur.execute(
                "INSERT INTO ability (name_en, name_fr, description_en, description_fr) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (name_en) DO UPDATE "
                "SET name_fr = EXCLUDED.name_fr, description_en = EXCLUDED.description_en, "
                "description_fr = EXCLUDED.description_fr",
                (ab["name_en"], ab.get("name_fr"), ab.get("description_en"), ab.get("description_fr")),
            )
        conn.commit()
        cur.execute("SELECT id, name_en FROM ability")
        rows = cur.fetchall()

    ability_map = {name.lower(): db_id for db_id, name in rows}
    LOGGER.info("Loaded %d abilities", len(ability_map))
    return ability_map


def load_moves(conn, moves: list[dict], type_map: dict) -> dict[str, int]:
    """Returns {name_en_lower: db_id}."""
    with conn.cursor() as cur:
        for m in moves:
            type_id = type_map.get(m.get("type_en", "").lower())
            if not type_id:
                LOGGER.warning("Unknown type '%s' for move '%s'", m.get("type_en"), m["name_en"])
                continue
            cur.execute(
                """INSERT INTO move
                   (name_en, name_fr, type_id, category, power, accuracy, pp,
                    description_en, description_fr, source)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (name_en) DO NOTHING""",
                (
                    m["name_en"], m.get("name_fr"), type_id,
                    m.get("category", "Status"),
                    m.get("power"), m.get("accuracy"), m.get("pp", 1),
                    m.get("description_en"), m.get("description_fr"),
                    m.get("source", "base"),
                ),
            )
        conn.commit()
        cur.execute("SELECT id, name_en FROM move")
        rows = cur.fetchall()

    move_map = {name.lower(): db_id for db_id, name in rows}
    LOGGER.info("Loaded %d moves", len(move_map))
    return move_map


def load_tms(conn, tms: list[dict], move_map: dict) -> None:
    with conn.cursor() as cur:
        for tm in tms:
            move_id = move_map.get(tm["move_name"].lower())
            if not move_id:
                LOGGER.warning("TM%02d: move '%s' not found", tm["number"], tm["move_name"])
                continue
            cur.execute(
                "INSERT INTO tm (number, move_id, location) VALUES (%s, %s, %s) "
                "ON CONFLICT (number) DO NOTHING",
                (tm["number"], move_id, tm.get("location")),
            )
        conn.commit()
    LOGGER.info("Loaded %d TMs", len(tms))


def load_pokemon(conn, pokedex: list[dict], stats: list[dict], gen_map: dict) -> dict[int, int]:
    """Returns {if_id: db_id} (db_id = if_id since it's the PK)."""
    stats_by_id = {s["if_id"]: s for s in stats}

    with conn.cursor() as cur:
        for entry in pokedex:
            if_id   = entry["if_id"]
            s       = stats_by_id.get(if_id, {})
            gen_id  = gen_map.get(entry.get("generation", 1), 1)

            cur.execute(
                """INSERT INTO pokemon
                   (id, national_id, name_en, name_fr, generation_id,
                    hp, attack, defense, sp_attack, sp_defense, speed,
                    base_experience, is_hoenn_only)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                (
                    if_id,
                    s.get("national_id"),
                    entry["name_en"],
                    s.get("name_fr"),
                    gen_id,
                    s.get("hp", 1),
                    s.get("attack", 1),
                    s.get("defense", 1),
                    s.get("sp_attack", 1),
                    s.get("sp_defense", 1),
                    s.get("speed", 1),
                    s.get("base_experience"),
                    entry.get("is_hoenn_only", False),
                ),
            )
        conn.commit()
    LOGGER.info("Loaded %d Pokémon", len(pokedex))
    return {e["if_id"]: e["if_id"] for e in pokedex}


def load_pokemon_types(conn, pokedex: list[dict], type_map: dict) -> None:
    with conn.cursor() as cur:
        for entry in pokedex:
            if_id = entry["if_id"]
            for slot, type_key in enumerate(
                [entry.get("type1"), entry.get("type2")], start=1
            ):
                if not type_key:
                    continue
                type_id = type_map.get(type_key.lower())
                if not type_id:
                    LOGGER.warning("Unknown type '%s' for Pokémon #%d", type_key, if_id)
                    continue
                cur.execute(
                    "INSERT INTO pokemon_type (pokemon_id, type_id, slot) "
                    "VALUES (%s, %s, %s) ON CONFLICT (pokemon_id, slot) DO NOTHING",
                    (if_id, type_id, slot),
                )
        conn.commit()
    LOGGER.info("Loaded Pokémon types")


def load_pokemon_abilities(conn, abilities: list[dict], ability_map: dict) -> None:
    """Load pokemon_ability rows from abilities_if.json pokemon lists."""
    pokemon_name_to_id: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute("SELECT id, name_en FROM pokemon")
        for db_id, name_en in cur.fetchall():
            pokemon_name_to_id[name_en.lower()] = db_id

    with conn.cursor() as cur:
        for ab in abilities:
            ability_id = ability_map.get(ab["name_en"].lower())
            if not ability_id:
                continue
            # Track slot per Pokémon: first normal=1, second normal=2, hidden=3
            slot_tracker: dict[int, int] = {}

            for poke in ab.get("pokemon", []):
                poke_id = pokemon_name_to_id.get(poke["name"].lower())
                if not poke_id:
                    continue

                if poke["is_hidden"]:
                    slot = 3
                else:
                    current = slot_tracker.get(poke_id, 0)
                    slot    = current + 1
                    slot_tracker[poke_id] = slot
                    if slot > 2:
                        continue   # only 2 normal slots

                cur.execute(
                    "INSERT INTO pokemon_ability (pokemon_id, ability_id, slot, is_hidden) "
                    "VALUES (%s, %s, %s, %s) ON CONFLICT (pokemon_id, slot) DO NOTHING",
                    (poke_id, ability_id, slot, poke["is_hidden"]),
                )
        conn.commit()
    LOGGER.info("Loaded Pokémon abilities")


def load_evolutions(conn, evolutions_base: list[dict]) -> None:
    """
    Load evolution data.
    Base evolutions come from PokeAPI (evolutions_base.json).
    IF overrides replace or augment those based on IF_EVOLUTION_OVERRIDES.
    """
    pokemon_name_to_id: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute("SELECT id, name_en FROM pokemon")
        for db_id, name_en in cur.fetchall():
            pokemon_name_to_id[name_en.lower()] = db_id

    with conn.cursor() as cur:
        for evo in evolutions_base:
            from_id  = pokemon_name_to_id.get(evo["from_name"].lower())
            into_id  = pokemon_name_to_id.get(evo["into_name"].lower())
            if not from_id or not into_id:
                continue

            key          = (evo["from_name"].lower(), evo["into_name"].lower())
            if_overrides = IF_EVOLUTION_OVERRIDES.get(key)

            if if_overrides:
                # Replace with IF-specific conditions
                for trigger, min_level, item, notes in if_overrides:
                    cur.execute(
                        """INSERT INTO pokemon_evolution
                           (pokemon_id, evolves_into_id, trigger_type, min_level,
                            item_name_en, if_override, if_notes)
                           VALUES (%s, %s, %s, %s, %s, TRUE, %s)
                           ON CONFLICT (pokemon_id, evolves_into_id, trigger_type, item_name_en)
                           DO NOTHING""",
                        (from_id, into_id, trigger, min_level, item, notes),
                    )
            else:
                # Base game evolution, unmodified
                trigger  = evo.get("trigger", "other")
                cur.execute(
                    """INSERT INTO pokemon_evolution
                       (pokemon_id, evolves_into_id, trigger_type, min_level, item_name_en)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (pokemon_id, evolves_into_id, trigger_type, item_name_en)
                       DO NOTHING""",
                    (from_id, into_id, trigger, evo.get("min_level"), evo.get("item")),
                )
        conn.commit()
    LOGGER.info("Loaded evolutions")


def load_locations(conn, locations_data: list[dict]) -> None:
    pokemon_name_to_id: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute("SELECT id, name_en FROM pokemon")
        for db_id, name_en in cur.fetchall():
            pokemon_name_to_id[name_en.lower()] = db_id

    location_map: dict[str, int] = {}
    with conn.cursor() as cur:
        for entry in locations_data:
            for loc in entry.get("locations", []):
                name = loc["name"]
                if name in location_map:
                    continue
                cur.execute(
                    "INSERT INTO location (name_en, region) VALUES (%s, %s) "
                    "ON CONFLICT (name_en) DO NOTHING RETURNING id",
                    (name, loc.get("region", "Other")),
                )
                row = cur.fetchone()
                if row:
                    location_map[name] = row[0]
        conn.commit()
        cur.execute("SELECT id, name_en FROM location")
        for db_id, name_en in cur.fetchall():
            location_map[name_en] = db_id

    with conn.cursor() as cur:
        for entry in locations_data:
            poke_id = pokemon_name_to_id.get(entry["pokemon_name"].lower())
            if not poke_id:
                continue
            for loc in entry.get("locations", []):
                loc_id = location_map.get(loc["name"])
                if not loc_id:
                    continue
                cur.execute(
                    "INSERT INTO pokemon_location (pokemon_id, location_id, method, notes) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (pokemon_id, location_id, method) DO NOTHING",
                    (poke_id, loc_id, loc.get("method", "wild"), loc.get("notes", "")),
                )
        conn.commit()
    LOGGER.info("Loaded locations")


def load_movesets(conn, movesets: list[dict], move_map: dict) -> None:
    """Load pokemon_move from movesets_merged.json (name_fr as key)."""
    # Build move_name_fr → move_id map
    move_fr_map: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute("SELECT id, name_fr FROM move WHERE name_fr IS NOT NULL")
        for db_id, name_fr in cur.fetchall():
            move_fr_map[name_fr.lower()] = db_id

    with conn.cursor() as cur:
        loaded = skipped = 0
        for record in movesets:
            move_id = move_fr_map.get(record["move_name_fr"].lower())
            if not move_id:
                skipped += 1
                continue

            cur.execute(
                """INSERT INTO pokemon_move
                   (pokemon_id, move_id, method, level, source)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (pokemon_id, move_id, method) DO NOTHING""",
                (
                    record["pokemon_if_id"],
                    move_id,
                    record["method"],
                    record.get("level"),
                    record.get("source", "base"),
                ),
            )
            loaded += 1
        conn.commit()
    LOGGER.info("Loaded %d moveset rows (%d skipped — move not found)", loaded, skipped)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    required = {
        "data/pokedex_if.json":      "extract_pokedex_if.py",
        "data/pokemon_stats.json":   "extract_stats_pokeapi.py",
        "data/moves_if.json":        "extract_moves_if.py",
        "data/tms_if.json":          "extract_moves_if.py",
        "data/abilities_if.json":    "extract_abilities_if.py",
        "data/locations_if.json":    "extract_locations_if.py",
        "data/movesets_merged.json": "transform_merge_movesets.py",
        "data/evolutions_base.json": "extract_stats_pokeapi.py",
    }
    for path, script in required.items():
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} not found — run {script} first")

    pokedex      = json.loads(Path("data/pokedex_if.json").read_text())
    stats        = json.loads(Path("data/pokemon_stats.json").read_text())
    moves        = json.loads(Path("data/moves_if.json").read_text())
    tms          = json.loads(Path("data/tms_if.json").read_text())
    abilities    = json.loads(Path("data/abilities_if.json").read_text())
    locations    = json.loads(Path("data/locations_if.json").read_text())
    movesets     = json.loads(Path("data/movesets_merged.json").read_text())
    evolutions   = json.loads(Path("data/evolutions_base.json").read_text())

    LOGGER.info("Connecting to PostgreSQL...")
    conn = get_pg_connection()

    gen_map     = load_generations(conn)
    type_map    = load_types(conn, moves)
    ability_map = load_abilities(conn, abilities)
    move_map    = load_moves(conn, moves, type_map)
    load_tms(conn, tms, move_map)
    load_pokemon(conn, pokedex, stats, gen_map)
    load_pokemon_types(conn, pokedex, type_map)
    load_pokemon_abilities(conn, abilities, ability_map)
    load_evolutions(conn, evolutions)
    load_locations(conn, locations)
    load_movesets(conn, movesets, move_map)

    conn.close()
    LOGGER.info("All data loaded successfully.")


if __name__ == "__main__":
    main()
