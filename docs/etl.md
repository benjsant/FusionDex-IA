# Pipeline ETL

Le pipeline ETL extrait les données depuis plusieurs sources externes, les transforme, puis les charge dans PostgreSQL. Il tourne en **mode one-shot** via `load_db.py` — pas encore de scheduler (Prefect prévu).

## Sources

| Source                     | Utilisée pour                                       |
| -------------------------- | --------------------------------------------------- |
| **PokeAPI** (REST)         | Stats de base, national dex IDs, learnsets TM/tutor |
| **Wiki IF** (MediaWiki)    | Fusions, Move Experts, mécaniques IF spécifiques    |
| **Poképédia** (MediaWiki)  | Noms FR                                             |
| **GitHub PokeAPI/sprites** | Sprites PNG statiques                               |

## Stack

- Python 3.12 + [`uv`](https://github.com/astral-sh/uv) (lockfile + venv)
- `requests` pour l'HTTP, `psycopg2-binary` + `sqlalchemy` pour la DB
- Parsers maison (wikitext) dans `etl/utils/wikitext.py`

## Séquence d'exécution

Le script principal [etl/scripts/load_db.py](https://github.com/) enchaîne une douzaine d'étapes :

1. **Initialisation** — création des tables via `init_postgres.sql` (si absentes).
2. **Types** — import des 18 types.
3. **Pokémon de base** — 501 espèces IF.
4. **Abilities + relations** — talents et leurs liens aux Pokémon.
5. **Moves + learnsets** — capacités et leur apprentissage.
6. **Évolutions** — chaînes evolve-into/evolve-from.
7. **Fusion sprites** — 166k lignes, fichiers disponibles sur le sidecar nginx.
8. **Créateurs** — attribution des sprites custom.
9. **Triple fusions** — les 23 cas reconnus.
10. **Locations** — zones de capture IF.
11. **Fix scripts** (correctifs canoniques post-import) :
    - `fix_national_ids.py`
    - `fix_stats_and_fr_names.py`
    - `fix_tms_from_pokeapi.py`
    - `fix_tutors_from_pokeapi.py`
    - `fix_pokemon_types.py`
    - `fix_move_experts.py`
12. **Audit** — comptages de cohérence (exposés via `/stats/coverage` côté API).

## Lancer le pipeline

```bash
cd etl
uv sync
uv run python -m etl.scripts.load_db
```

!!! warning "Requiert la DB up"
    Le pipeline se connecte à Postgres via `DATABASE_URL` (cf. `.env`). Lance d'abord `docker compose up -d db` si tu pars de zéro.

## Patterns récurrents

### Cache de requêtes wiki

Les pages MediaWiki sont longues à fetch. Chaque script met en cache le wikitext brut sous `etl/data/cache/` pour éviter de requêter à chaque relance.

### Normalisation de noms

Les sources divergent sur quelques noms (ex : wiki IF écrit *Flaafy* au lieu de *Flaaffy*). Chaque parseur expose un dictionnaire d'alias + une fonction `norm()` qui strip espaces, `-`, `'`, `.` et lowercase pour matcher contre la DB.

```python
WIKI_POKEMON_ALIASES = {"flaafy": "flaaffy"}

def norm_pokemon(name: str) -> str:
    n = norm(name)
    return WIKI_POKEMON_ALIASES.get(n, n)
```

### Parsing de tables avec rowspan

Les Move Experts et plusieurs autres pages wiki utilisent `rowspan` pour factoriser les cellules partagées entre plusieurs lignes. Le parseur maison reconstruit la matrice complète avant d'extraire les données.

### Idempotence

Les scripts `fix_*.py` sont réexécutables : ils font du `UPSERT` (SQL `ON CONFLICT DO UPDATE`) ou un `DELETE` + `INSERT` pour les tables dont ils sont seuls responsables (`move_expert_move`).

## Voir aussi

- [Base de données](database.md) — schéma cible.
- [Roadmap](roadmap.md) — audit DB et mega-évolutions restent à traiter.
