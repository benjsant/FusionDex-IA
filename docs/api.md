# API backend

FastAPI exposant 30+ endpoints. Swagger interactif en dev : [http://localhost:58000/docs](http://localhost:58000/docs).

En prod le backend n'est **pas** exposé publiquement — les requêtes passent par le proxy Next.js (`/api/*` sur le domaine public).

## Organisation

```
backend/
  main.py                 # wiring FastAPI + CORS
  routes/                 # endpoints HTTP (une file par domaine)
  services/               # logique métier + accès DB
  schemas/                # Pydantic — contrat I/O
  db/
    models/               # SQLAlchemy
    base.py               # engine + session
  tests/                  # pytest + TestClient (53 tests verts)
```

Chaque `route` importe son `service`, qui importe ses `models` et `schemas`. Les routes ne touchent jamais directement SQLAlchemy.

## Endpoints principaux

### Pokémon

| Méthode | Chemin                                          | Description                               |
| ------- | ----------------------------------------------- | ----------------------------------------- |
| GET     | `/pokemon/`                                     | Liste paginée + filtres type/gen          |
| GET     | `/pokemon/{id}`                                 | Fiche complète                            |
| GET     | `/pokemon/{id}/moves`                           | Learnset (level-up + TM + tutor + egg)    |
| GET     | `/pokemon/{id}/evolutions`                      | Chaîne pre + post                         |
| GET     | `/pokemon/{id}/locations`                       | Zones de capture                          |
| GET     | `/pokemon/{id}/weaknesses`                      | Matchups défensifs                        |

### Moves / Abilities / Types

| Méthode | Chemin                     | Description                      |
| ------- | -------------------------- | -------------------------------- |
| GET     | `/moves/`                  | Liste paginée + filtres          |
| GET     | `/moves/{id}`              | Détail + Pokémon qui apprennent  |
| GET     | `/abilities/`              | Liste                            |
| GET     | `/abilities/{id}`          | Détail + Pokémon porteurs        |
| GET     | `/types/`                  | 18 types + matchups              |

### Fusions

| Méthode | Chemin                                      | Description                                    |
| ------- | ------------------------------------------- | ---------------------------------------------- |
| GET     | `/fusion/{head_id}/{body_id}`               | Calcul de la fusion (stats, types, moves…)     |
| GET     | `/fusion/{head_id}/{body_id}/moves`         | Learnset de la fusion                          |
| GET     | `/fusion/{head_id}/{body_id}/abilities`     | Talents combinés                               |
| GET     | `/fusion/{head_id}/{body_id}/weaknesses`    | Matchups défensifs                             |
| GET     | `/fusion/{head_id}/{body_id}/expert-moves`  | Moves débloqués par les Move Experts           |
| GET     | `/fusion/random`                            | Fusion aléatoire                               |
| GET     | `/fusions/involving/{pokemon_id}`           | Toutes les paires où ce Pokémon intervient     |

### Sprites

| Méthode | Chemin                                     | Description                                   |
| ------- | ------------------------------------------ | --------------------------------------------- |
| GET     | `/sprites/{head_id}/{body_id}/image`       | PNG — default ou `?variant_id=N`              |
| GET     | `/sprites/{head_id}/{body_id}/variants`    | Liste des variantes + crédits                 |

### Méta

| Méthode | Chemin                              | Description                                    |
| ------- | ----------------------------------- | ---------------------------------------------- |
| GET     | `/generations/`                     | Liste des 9 générations                        |
| GET     | `/generations/{id}/pokemon`         | Pokémon d'une génération                       |
| GET     | `/creators/`                        | Créateurs de sprites                           |
| GET     | `/creators/{id}/sprites`            | Sprites d'un créateur                          |
| GET     | `/triple-fusions/`                  | 23 fusions triples                             |
| GET     | `/stats/coverage`                   | Audit de complétude                            |
| GET     | `/health`                           | Healthcheck                                    |

### IA

| Méthode | Chemin      | Description                                                    |
| ------- | ----------- | -------------------------------------------------------------- |
| POST    | `/ai/ask`   | Question en langage naturel → réponse DeepSeek (503 sans clé)  |

## CORS

Défense en profondeur uniquement — le flux principal passe par le proxy Next.js (même origine).

```python
# backend/main.py
cors_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:53000,http://localhost:58000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

En prod, `CORS_ALLOWED_ORIGINS` doit lister uniquement le domaine public.

## Tests

53 tests pytest + `TestClient`. Ils nécessitent un dump SQL sous `backend/tests/fixtures/` (actuellement non committé — seul `test_ai.py` tourne en CI).

```bash
cd backend
uv run pytest
```

## Voir aussi

- [Règles de fusion](fusion-rules.md) — sémantique des endpoints `/fusion/*`.
- [Architecture](architecture.md) — flux de requêtes.
