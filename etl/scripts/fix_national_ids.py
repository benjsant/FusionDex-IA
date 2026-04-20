"""
Script de correction — aligne `pokemon.national_id` sur le vrai ID national
PokeAPI en se fiant au nom anglais (issu de `data/pokedex_if.json`, source
autoritaire pour la numérotation Infinite Fusion).

Contexte : `extract_stats_pokeapi.py` posait `national_id = if_id`, ce qui est
correct jusqu'à Celebi (#251) mais faux ensuite — la Pokédex IF diverge de
la Pokédex nationale (Shinx/Lixy est if_id 388 mais national 403, etc.).
Conséquence : ~320 lignes ont un mauvais national_id, d'où des stats, types,
sprites et noms FR incohérents.

Ce script corrige uniquement `national_id`. Le reste (types, stats, name_fr)
devra être re-synchronisé ensuite via les scripts dédiés.

Normalisation des noms : conforme à l'API (`/api/v2/pokemon/{name}`) — tout
minuscule, apostrophes et points retirés, ♀/♂ mappés en -f/-m, formes
alternatives mappées à leur variant par défaut.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

from etl.utils.db import pg_connection
from etl.utils.logging import setup_logging

LOGGER = setup_logging(__name__)

POKEDEX_IF_JSON = Path(__file__).resolve().parents[2] / "data" / "pokedex_if.json"
POKEAPI_SPECIES = "https://pokeapi.co/api/v2/pokemon-species/{}"
REQUEST_DELAY = 0.12  # sec. entre requêtes

# Mapping manuel pour les cas que la normalisation auto ne couvre pas.
# Clé : name_en tel qu'il apparaît dans pokedex_if.json.
# Valeur : slug PokeAPI OU int national_id (si pas dans PokeAPI).
MANUAL_OVERRIDES: dict[str, str | int] = {
    # Formes avec caractères spéciaux
    "Nidoran♀": "nidoran-f",
    "Nidoran♂": "nidoran-m",
    "Farfetch'd": "farfetchd",
    "Mr. Mime": "mr-mime",
    "Mime Jr.": "mime-jr",
    "Mr. Rime": "mr-rime",
    "Type: Null": "type-null",
    "Jangmo-o": "jangmo-o",
    "Hakamo-o": "hakamo-o",
    "Kommo-o": "kommo-o",
    "Ho-Oh": "ho-oh",
    "Porygon-Z": "porygon-z",
    "Porygon2": "porygon2",
    "Flabébé": "flabebe",
    # Formes IF custom sans équivalent PokeAPI — laisser national_id NULL.
    # (on n'ajoute pas d'override, le script détectera l'absence et skip.)
}

# Valeurs spéciales : skip entièrement (IF-only, triple fusions, formes custom)
SKIP_NAMES: set[str] = set()


def normalize_name(name_en: str) -> str:
    """Convertit un name_en vers le slug PokeAPI."""
    n = name_en.lower()
    # Suppression accents basiques pour certains cas (é, è, â…)
    n = (
        n.replace("é", "e")
         .replace("è", "e")
         .replace("ê", "e")
         .replace("à", "a")
         .replace("â", "a")
         .replace("ô", "o")
         .replace("û", "u")
         .replace("î", "i")
         .replace("ï", "i")
    )
    n = n.replace("'", "").replace(".", "").replace(" ", "-")
    return n


def resolve_slug(name_en: str) -> str | int | None:
    """Retourne le slug PokeAPI, un national_id direct, ou None si à skipper."""
    if name_en in SKIP_NAMES:
        return None
    if name_en in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[name_en]
    return normalize_name(name_en)


def fetch_national_id(slug: str) -> int | None:
    """Interroge PokeAPI `/pokemon-species/{slug}` (renvoie l'ID national)."""
    try:
        resp = requests.get(POKEAPI_SPECIES.format(slug), timeout=10)
        if resp.status_code != 200:
            return None
        return int(resp.json()["id"])
    except Exception as e:
        LOGGER.warning("PokeAPI erreur pour slug=%s : %s", slug, e)
        return None


def load_pokedex_if() -> dict[int, str]:
    """Charge pokedex_if.json → {if_id: name_en}."""
    with POKEDEX_IF_JSON.open(encoding="utf-8") as f:
        data = json.load(f)
    return {entry["if_id"]: entry["name_en"] for entry in data}


def fix_national_ids(conn) -> None:
    cur = conn.cursor()

    pokedex_if = load_pokedex_if()
    LOGGER.info("%d entrées chargées depuis pokedex_if.json", len(pokedex_if))

    cur.execute("SELECT id, national_id, name_en FROM pokemon ORDER BY id")
    db_rows = cur.fetchall()
    LOGGER.info("%d Pokémon en base", len(db_rows))

    updated = unchanged = unresolved = skipped = 0
    unresolved_names: list[tuple[int, str]] = []
    # 1) Première passe : récolte (pk_id, target_national_id). On ne fait AUCUN
    #    UPDATE ici pour éviter de violer temporairement la contrainte UNIQUE.
    updates: list[tuple[int, int | None]] = []

    for pokemon_id, current_national, name_en in db_rows:
        # Vérifie que le name_en en base matche bien pokedex_if.json
        expected_name = pokedex_if.get(pokemon_id)
        if expected_name and expected_name != name_en:
            LOGGER.warning(
                "Pokémon id=%d : name_en DB='%s' ≠ pokedex_if='%s' — on fait confiance à pokedex_if",
                pokemon_id, name_en, expected_name,
            )
            name_en = expected_name

        slug_or_id = resolve_slug(name_en)
        if slug_or_id is None:
            skipped += 1
            updates.append((pokemon_id, None))
            continue

        if isinstance(slug_or_id, int):
            target = slug_or_id
        else:
            target = fetch_national_id(slug_or_id)
            time.sleep(REQUEST_DELAY)
            if target is None:
                unresolved += 1
                unresolved_names.append((pokemon_id, name_en))
                updates.append((pokemon_id, None))  # on nullifiera
                continue

        updates.append((pokemon_id, target))

    # 2) Résolution des collisions — plusieurs if_id peuvent pointer vers un
    #    même national_id (ex. formes alternatives). On garde le plus petit
    #    if_id et on met les autres à NULL.
    by_target: dict[int, list[int]] = {}
    for pk_id, target in updates:
        if target is not None:
            by_target.setdefault(target, []).append(pk_id)

    collisions: set[int] = set()
    for target, pks in by_target.items():
        if len(pks) > 1:
            keep = min(pks)
            for pk in pks:
                if pk != keep:
                    collisions.add(pk)
            LOGGER.warning(
                "Collision national_id=%d : garde pk=%d, NULL pour %s",
                target, keep, [pk for pk in pks if pk != keep],
            )

    # 3) Applique : on commence par TOUT mettre à NULL, puis on pose les
    #    valeurs cibles. Évite les conflits UNIQUE pendant la transition.
    cur.execute("UPDATE pokemon SET national_id = NULL")
    LOGGER.info("national_id vidé pour toutes les lignes")

    for pk_id, target in updates:
        if target is None or pk_id in collisions:
            continue
        cur.execute(
            "UPDATE pokemon SET national_id = %s WHERE id = %s",
            (target, pk_id),
        )
        # Comptabilise changé vs inchangé par rapport à l'état initial
        # (avant le UPDATE ... = NULL)
        initial = next((n for i, n, _ in db_rows if i == pk_id), None)
        if initial == target:
            unchanged += 1
        else:
            updated += 1

    conn.commit()

    LOGGER.info(
        "Terminé — %d mis à jour | %d inchangés | %d non résolus | %d ignorés | %d collisions NULL",
        updated, unchanged, unresolved, skipped, len(collisions),
    )
    if unresolved_names:
        LOGGER.warning("Noms non résolus (à traiter en override) :")
        for pk_id, name in unresolved_names:
            LOGGER.warning("  id=%d name_en=%s", pk_id, name)

    cur.close()


def main() -> None:
    with pg_connection() as conn:
        fix_national_ids(conn)


if __name__ == "__main__":
    main()
